from django.db import models

# from django.contrib.gis.db import models
from datetime import datetime, timedelta
from django.utils.html import format_html
import os, sys
import subprocess
import string
import hashlib
import time
import socket
import re
import pwd, grp
import dns.resolver

##from fields import *  # custom MultiSelectField, MultiSelectFormField from http://djangosnippets.org/snippets/2753/
from multiselectfield import MultiSelectField

from sizefield.models import FileSizeField
from sizefield.templatetags.sizefieldtags import filesize

# needed for volume feed
from django.contrib.syndication.views import Feed

# Needed for BigInteger fix
from django.db.models.fields import IntegerField
from django.conf import settings

from django.contrib.auth.models import *

from django.core.validators import RegexValidator

# https://timmyomahony.com/blog/reversing-admin-urls-and-creating-admin-links-you-models/
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse


class Tenancy(models.Model):
    name = models.CharField(max_length=80)
    summary = models.CharField(max_length=80)

    def __str__(self):
        return self.name

    class Meta:
        ordering = ["name"]


class Person(models.Model):
    """Person with some role"""

    name = models.CharField(max_length=1024, help_text="Firstname Lastname")
    email = models.EmailField(help_text="Email address")
    username = models.CharField(max_length=45, help_text="System username")

    def __str__(self):
        return "%s" % self.name

    class Meta:
        ordering = ["name"]


class VMRequest(models.Model):
    vm_name = models.CharField(
        max_length=127, help_text="proposed fully-qualified host name"
    )  # TODO : need regex
    type = models.CharField(
        max_length=16, choices=settings.VM_TYPE_CHOICES, help_text="Type of VM, see REF"
    )  # TODO update REF
    operation_type = models.CharField(
        max_length=127,
        choices=settings.VM_OP_TYPE_CHOICES,
        help_text="Operation type of VM (dev, test, production, ...)",
    )
    internal_requester = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="CEDA person sponsoring the request",
        related_name="vmrequest_internal_requester_user",
    )
    description = models.TextField(help_text="")
    date_required = models.DateField()
    cpu_required = models.CharField(
        max_length=127, choices=settings.VM_CPU_REQUIRED_CHOICES
    )
    memory_required = models.CharField(
        max_length=127, choices=settings.VM_MEM_REQUIRED_CHOICES
    )
    disk_space_required = models.CharField(
        max_length=127, choices=settings.VM_DISK_SPACE_REQUIRED_CHOICES
    )
    disk_activity_required = models.CharField(
        max_length=127, choices=settings.VM_DISK_ACTIVITY_REQUIRED_CHOICES
    )
    mountpoints_required = MultiSelectField(
        max_length=2048, choices=settings.MOUNT_CHOICES
    )
    network_required = models.CharField(
        max_length=127, choices=settings.VM_NETWORK_ACTIVITY_REQUIRED_CHOICES
    )
    os_required = models.CharField(
        max_length=127, choices=settings.VM_OS_REQUIRED_CHOICES, default="rocky9"
    )
    other_info = models.TextField(blank=True)
    patch_responsible = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vmrequest_patch_responsible_user",
        limit_choices_to={"id__in": settings.ADMIN_USERS_PATCH_RESPONSIBLE},
    )
    root_users = models.ManyToManyField(User, related_name="vmrequest_root_users_user")
    request_type = models.CharField(
        max_length=127, choices=settings.VM_REQUEST_TYPE_CHOICES, default="new"
    )
    request_status = models.CharField(
        max_length=127, choices=settings.VM_REQUEST_STATUS_CHOICES, default="pending"
    )
    vm = models.ForeignKey(
        "VM",
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
        help_text="VM to which this request pertains",
    )
    end_of_life = models.DateField(
        default=datetime.now() + timedelta(days=3 * 365)
    )  # approx 3 years from now
    timestamp = models.DateTimeField(
        auto_now=True, auto_now_add=False, help_text="time last modified"
    )

    tenancy = models.ForeignKey(
        Tenancy, on_delete=models.PROTECT, null=True, blank=True
    )

    # Set default ordering
    class Meta:
        ordering = ["vm_name"]

    def __str__(self):
        return "%s" % self.vm_name

    def action_links(self):
        if self.request_status == "ceda pending":
            return format_html(
                '<a href="/vmrequest/%i/approve">approve</a>|<a href="/vmrequest/%i/reject">reject</a>'
                % (self.id, self.id)
            )
        elif self.request_status == "ceda approved":
            return format_html('<a href="/vmrequest/%i/convert">convert</a>' % self.id)
        else:
            return "n/a"

    action_links.allow_tags = True
    action_links.short_description = "actions"

    def reject(self):
        """Review process : reject a request"""
        if self.request_status == "ceda pending":
            self.request_status = "ceda rejected"
            # disassociate it from any gws
            self.vm = None
            self.save()

        else:
            raise Exception("Can't reject a request unless status = 'ceda pending'")

    def approve(self):
        """Review process : approve a request"""
        if self.request_status == "ceda pending":
            self.request_status = "ceda approved"
            # disassociate it from any gws
            self.save()
        else:
            raise Exception("Can't approve a request unless status = 'ceda pending'")

    def convert(self):
        """Set the status to completed. If no associated VM, make one and associate this request with it. Else update an existing VM. In both cases, copy existing fields to overwrite attributes of VM."""

        # Approving a new request (first time)
        if self.request_type == "new":  # and (self.vm is None or self.vm == ''):
            # make a new gws object, copying attributes from request
            vm = VM.objects.create(
                name=self.vm_name,
                internal_requester=self.internal_requester,
                description=self.description,
                date_required=self.date_required,
                type=self.type,
                operation_type=self.operation_type,
                cpu_required=self.cpu_required,
                memory_required=self.memory_required,
                disk_space_required=self.disk_space_required,
                disk_activity_required=self.disk_activity_required,
                mountpoints_required=self.mountpoints_required,
                network_required=self.network_required,
                os_required=self.os_required,
                patch_responsible=self.patch_responsible,
                status="active",
                end_of_life=self.end_of_life,
                other_info=self.other_info,
                tenancy=self.tenancy,
            )
            # root_users is a ManyToManyField, so need to copy outside of create()
            vm.forceSave()

            for user in self.root_users.all():
                vm.root_users.add(user)
            vm.forceSave()

            self.vm = vm
            # update the request status
            self.request_status = "completed"
            self.save()

        elif self.request_type == "update":
            if self.vm is None or self.vm == "":
                raise Exception("Can't do update request : no VM associated")
            else:
                vm = self.vm
                print((self.vm))
                # update the existing associated vm
                vm.name = self.vm_name
                vm.internal_requester = self.internal_requester
                vm.description = self.description
                vm.date_required = self.date_required
                vm.type = self.type
                vm.operation_type = self.operation_type
                vm.cpu_required = self.cpu_required
                vm.memory_required = self.memory_required
                vm.disk_space_required = self.disk_space_required
                vm.disk_activity_required = self.disk_activity_required
                vm.mountpoints_required = self.mountpoints_required
                vm.network_required = self.network_required
                vm.os_required = self.os_required
                vm.patch_responsible = self.patch_responsible
                vm.status = "active"
                vm.end_of_life = self.end_of_life
                vm.other_info = self.other_info
                vm.tenancy = self.tenancy
                vm.forceSave()

                for user in self.root_users.all():
                    vm.root_users.add(user)

                vm.forceSave()

                # update the request status
                self.request_status = "completed"
                self.save()

        elif self.request_type == "remove":
            if self.vm is None or self.vm == "":
                raise Exception("Can't do update request : no VM associated")
            else:
                self.vm.status = "retired"
                self.vm.retired = datetime.now()
                self.request_status = "completed"

                self.vm.forceSave()
                self.save()

        else:
            raise Exception(
                "Must set request status to update if updating an existing VM"
            )

    def vm_link(self):
        if self.vm is not None:
            return format_html(
                '<a href="/admin/cedainfoapp/vm/%i">%s</a>' % (self.vm.id, self.vm.name)
            )

    vm_link.allow_tags = True
    vm_link.short_description = "VM"

    def coloured_vm_name(self):
        """Colour the vm name if no dns entry found"""

        try:
            address = socket.gethostbyname(self.vm_name)
            return self.vm_name
        except:
            return format_html('<span style="color:red;">%s</span>' % self.vm_name)

    coloured_vm_name.short_description = "VM name"
    coloured_vm_name.allow_tags = True


class VM(models.Model):
    name = models.CharField(
        max_length=127, help_text="fully-qualified host name", unique=True
    )  # TODO : need regex
    type = models.CharField(
        max_length=16, choices=settings.VM_TYPE_CHOICES, help_text="Type of VM, see REF"
    )  # TODO update REF
    operation_type = models.CharField(
        max_length=127,
        choices=settings.VM_OP_TYPE_CHOICES,
        help_text="Operation type of VM (dev, test, production, ...)",
    )
    internal_requester = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        help_text="CEDA person sponsoring the request",
        related_name="vm_internal_requester_user",
    )
    description = models.TextField(help_text="")
    date_required = models.DateField()
    cpu_required = models.CharField(
        max_length=127, choices=settings.VM_CPU_REQUIRED_CHOICES
    )
    memory_required = models.CharField(
        max_length=127, choices=settings.VM_MEM_REQUIRED_CHOICES
    )
    disk_space_required = models.CharField(
        max_length=127, choices=settings.VM_DISK_SPACE_REQUIRED_CHOICES
    )
    disk_activity_required = models.CharField(
        max_length=127, choices=settings.VM_DISK_ACTIVITY_REQUIRED_CHOICES
    )
    mountpoints_required = MultiSelectField(
        max_length=2048, choices=settings.MOUNT_CHOICES
    )
    network_required = models.CharField(
        max_length=127, choices=settings.VM_NETWORK_ACTIVITY_REQUIRED_CHOICES
    )
    os_required = models.CharField(
        max_length=127, choices=settings.VM_OS_REQUIRED_CHOICES, default="rhel7"
    )
    other_info = models.TextField(blank=True)
    patch_responsible = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="vm_patch_responsible_user",
        limit_choices_to={"id__in": settings.ADMIN_USERS_PATCH_RESPONSIBLE},
    )
    root_users = models.ManyToManyField(User, related_name="vm_root_users_user")
    status = models.CharField(
        max_length=127, choices=settings.VM_STATUS_CHOICES, default="active"
    )
    created = models.DateField(auto_now_add=True)
    end_of_life = models.DateField(
        default=datetime.now() + timedelta(days=3 * 365)
    )  # 3 years from now
    retired = models.DateField(null=True, blank=True)
    timestamp = models.DateTimeField(
        auto_now=True, auto_now_add=False, help_text="time last modified"
    )
    tenancy = models.ForeignKey(
        Tenancy, on_delete=models.PROTECT, null=True, blank=True
    )

    ping_last_ok = models.DateField(blank=True)

    # Set default ordering
    class Meta:
        ordering = ["name"]

    def __str__(self):
        return "%s" % self.name

    def save(self, *args, **kwargs):
        # Custom save method : will only save an instance if there is no PK, i.e. if the model is a new instance
        # Logic : If you want to change a request, you can't, you need to make a new one & have that approved.
        super(VM, self).save(*args, **kwargs)

    #       if self.pk is None:
    #           super(VM, self).save(*args, **kwargs)
    #       else:
    #           raise Exception("Unable to save changes to existing VM : create an update request & get it approved")

    def forceSave(self, *args, **kwargs):
        # OK, sometimes we need to update individual fields (e.g. "approved")"
        super(VM, self).save(*args, **kwargs)

    def create_update_request(self):
        """Create a new gwsrequest based on this gws pre-populated with values ready for editing & approval"""
        req = VMRequest.objects.create(
            vm_name=self.name,
            internal_requester=self.internal_requester,
            description=self.description,
            date_required=self.date_required,
            type=self.type,
            operation_type=self.operation_type,
            cpu_required=self.cpu_required,
            memory_required=self.memory_required,
            disk_space_required=self.disk_space_required,
            disk_activity_required=self.disk_activity_required,
            mountpoints_required=self.mountpoints_required,
            network_required=self.network_required,
            os_required=self.os_required,
            patch_responsible=self.patch_responsible,
            request_status="ceda pending",
            request_type="update",
            end_of_life=self.end_of_life,
            tenancy=self.tenancy,
            vm=self,
        )
        req.save()
        for user in self.root_users.all():
            req.root_users.add(user)
        req.save()
        return req.id

    def update_link(self):
        return '<a href="/vm/%i/update">update</a>' % self.id

    update_link.allow_tags = True

    def change_status(self):
        """Cycle thro the available VM_STATUS_CHOICES (created / inuse / deprecated / retired)"""
        status_options = settings.VM_STATUS_CHOICES
        current_index = 0
        for i in status_options:
            # lookup position of current status value in tuple
            if self.status == i[0]:
                break
            current_index += 1
        # select the next entry from the tuple
        try:
            self.status = status_options[current_index + 1][0]
        except IndexError:
            self.status = status_options[0][0]
        self.forceSave()

    def action_links(self):
        return format_html(
            '<a href="/vm/%i/changestatus">change status</a>' % (self.id,)
        )

    action_links.allow_tags = True
    action_links.short_description = "actions"

    def dns_ok(self):
        """Returns True if dns entry found for vm"""

        if self.name.startswith("00 "):
            return True

        try:
            address = socket.gethostbyname(self.name.replace("legacy:", ""))
            return True
        except:
            return False

    def cname(self):
        """Returns True if there is a cname for this vm name"""

        if self.name.startswith("00 "):
            return False

        try:
            host = self.name.replace("legacy:", "")
            result = dns.resolver.query(host, "CNAME")
            return True
        except:
            return False

    def ping_check(self):
        """Performs ping check on host. If successful records the time in the 'ping_last_ok' attribute and returns True"""

        if self.ping_ok():
            #
            #         Save the update using a queryset so that the timestamp of the VM object is not updated as well
            #
            VM.objects.filter(name=self.name).update(ping_last_ok=datetime.now())

            return True
        else:
            return False

    def ping_ok(self):
        """Returns True if VM can be pinged"""

        name = self.name
        name = name.replace("legacy:", "")

        FNULL = open(os.devnull, "w")
        status = subprocess.call(["ping", "-c 1", name], stdout=FNULL, stderr=FNULL)
        FNULL.close()

        if status == 0:
            return True
        else:
            return False

    #

    # def coloured_vm_name(self):
    #     '''Colour the vm name if no dns entry found. Remove legacy prefix before checking'''
    #     try:
    #         address = socket.gethostbyname(self.name.replace('legacy:', ''))
    #         return self.name
    #     except:
    #         return (format_html('<span style="color:red;">%s</span>' % self.name))

    def coloured_vm_name(self):
        """Colour the vm name if no dns entry found. Remove legacy prefix before checking."""
        try:
            name = self.name.replace("legacy:", "")
            result = dns.resolver.query(name, "A")
            try:
                result = dns.resolver.query(name, "CNAME")
                return format_html('<span style="color:olive;">%s</span>' % self.name)
            except:
                pass
            return self.name
        except:
            return format_html('<span style="color:red;">%s</span>' % self.name)

    def service_count(self):
        production_count = len(
            NewService.objects.filter(host_id=self.id, status="production")
        )
        decomissioned_count = len(
            NewService.objects.filter(host_id=self.id, status="decomissioned")
        )

        return '<a href="/admin/cedainfoapp/newservice/?Host=%s">%s (%s)</a>' % (
            self.id,
            production_count,
            decomissioned_count,
        )

    service_count.allow_tags = True
    ##    service_count.admin_order_field='service_count'

    coloured_vm_name.short_description = "VM name"
    coloured_vm_name.allow_tags = True


class ServiceKeyword(models.Model):
    keyword = models.CharField(max_length=30)

    def __str__(self):  # __str__ on Python 2
        return self.keyword

    class Meta:
        ordering = ("keyword",)



class NewService(models.Model):
    """Software-based service"""

    # host = models.ManyToManyField(Host, help_text="Host machine on which service is deployed", null=True, blank=True)
    host = models.ForeignKey(
        VM,
        on_delete=models.PROTECT,
        help_text="Host machine on which service is deployed",
        null=True,
        blank=False,
    )
    name = models.CharField(max_length=512, help_text="Name of service")
    url = models.URLField(max_length=200, help_text="", default="", blank=True)
    uptimerobot_monitor_id = models.IntegerField(
        help_text='ID number of UptimeRobot monitor for this service. See <a href="/services/uptimerobot">See UptimeRobot monitors</a> and <a href="/services/uptimerobot-check">UptimeRobot service check</a>',
        blank=True,
    )
    status = models.CharField(
        max_length=50,
        choices=(
            ("pre-production", "Pre-production"),
            ("production", "Production"),
            ("decomissioned", "Decomissioned"),
            ("other", "Other (e.g. temporarily offline)"),
        ),
        default="to be reviewed",
    )

    priority = models.CharField(
        max_length=50,
        choices=(("low", "Low"), ("medium", "Medium"), ("high", "High")),
        default="Low",
    )

    description = models.TextField(blank=True, help_text="Longer description if needed")
    documentation = models.URLField(
        blank=True, help_text="URL to documentation for service in opman"
    )
    ##    externally_visible = models.BooleanField(default=False, help_text="Whether or not this service is visible outside the RAL firewall")

    visibility = models.CharField(
        max_length=50,
        choices=(
            ("public", "Public"),
            ("internal", "Internal only"),
            ("restricted", "Restricted external access"),
        ),
        default="public",
        help_text="Intended visibility when operational",
    )

    service_manager = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="software_manager",
        help_text="CEDA person who looks after this service",
    )

    deputy_service_manager = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="deputy_service_manager",
        help_text="Deputy for service manager",
    )

    owner = models.ForeignKey(
        Person,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="owner",
        help_text="Owner of this service",
    )

    startdate = models.DateField(
        null=True, blank=True, help_text="Approximate date service went into production"
    )
    last_reviewed = models.DateField(
        null=True, blank=True, help_text="Date of last review"
    )
    review_status = models.CharField(
        max_length=50,
        choices=(
            ("to be reviewed", "To be reviewed"),
            ("passed", "Passed"),
            ("passed with issues", "Passed with issues"),
            ("failed", "Failed"),
            ("failed with minor issues", "Failed with minor issues"),
        ),
        default="to be reviewed",
    )

    review_info = models.TextField(
        blank=True,
        help_text="Information from reviews. Please date and put most recent information at the top.",
    )

    keywords = models.ManyToManyField(
        ServiceKeyword,
        blank=True,
        null=True,
        help_text="Select any keywords that apply to this service",
    )

    ports = models.CharField(
        max_length=100,
        blank=True,
        help_text="External open ports required by this service",
    )

    class Meta:
        verbose_name = "Service"

    def __str__(self):
        theHost = ""
        if self.host is not None:
            theHost = self.host
        return "%s (%s)" % (self.name, theHost)

    def summary(self):
        """Returns a summary string extracted from the start of the full description text"""

        SummaryLength = 60
        summary = self.description.strip()
        summary = " ".join(summary.split())

        if len(summary) > SummaryLength:
            summary = summary[0 : SummaryLength - 1] + "..."

        return summary

    def documentationLink(self):
        return self.documentation

    def coloured_vm_name(self):
        """Colour the vm name if no dns entry found. Remove legacy prefix before checking"""

        vm = self.host

        try:
            address = socket.gethostbyname(vm.name.replace("legacy:", ""))
            #         address = socket.gethostbyname(vm.name)

            return vm
        except:
            return '<span style="color:red;">%s</span>' % vm

    coloured_vm_name.short_description = "VM name"
    coloured_vm_name.allow_tags = True
