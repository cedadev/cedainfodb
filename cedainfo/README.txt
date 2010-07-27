Deploying the CEDA Info DB.

Each deployment should have it's own "settings.py" configuration file in the based directory.
If there isn't one for a particular deployment already "settings.py.template" can be used to create a new one.
You should not check in to the SVN repository any deployment-specific "settings.py" files (in fact there is an svn:ignore property to prevent this) but to ensure that these settings are version controlled you should save a copy into the higher level "deployment_settings" directory which is version controlled. 