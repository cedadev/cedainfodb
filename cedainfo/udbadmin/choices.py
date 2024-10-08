'''
BSD Licence
Copyright (c) 2012, Science & Technology Facilities Council (STFC)
All rights reserved.

Redistribution and use in source and binary forms, with or without modification, 
are permitted provided that the following conditions are met:

    * Redistributions of source code must retain the above copyright notice, 
        this list of conditions and the following disclaimer.
    * Redistributions in binary form must reproduce the above copyright notice,
        this list of conditions and the following disclaimer in the documentation
        and/or other materials provided with the distribution.
    * Neither the name of the Science & Technology Facilities Council (STFC) 
        nor the names of its contributors may be used to endorse or promote 
        products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" 
AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, 
THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR 
PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, 
OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF 
SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE 
OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

Created on 28 Nov 2012

@author: Andrew Harwood
@author: Maurizio Nagni
'''
DATASET_REGISTRATION_TYPES=(

   ("manual","manual"),
   ("online","online"),
   ("public","public"),
   ("signature", "signature"),
   ("badc", "badc"),
   ("reguser", "reguser"),
   ("jasmin-portal", "jasmin-portal"),
   ("none", "none")
)

DATACENTRES=(
   ("badc", "badc"),
   ("neodc", "neodc")
)

FUNDING_TYPES=(
   ("", ""),   
   ("NERC", "NERC"),
   ("AHRC", "AHRC"),
   ("BBSRC", "BBSRC"),
   ("EPSRC", "EPSRC"),
   ("ESRC", "ESRC"),
   ("MRC", "MRC"),
   ("STFC", "STFC"),
   ("Non-UK academic funding", "Non-UK academic funding"),
   ("Government department", "Government department"),
   ("Charitable trust", "Charitable trust"),
   ("Commercial", "Commercial"),
   ("Not funded", "Not funded"),
   ("Other", "Other")
)

INSTITUTE_TYPES=(
   ("Commercial", "Commercial"),
   ("Government", "Government"),
   ("NERC", "NERC"),
   ("School", "School"),
   ("University", "University"),
   ("Other", "Other")
)

NERC_FUNDED=(
   (0, "No"),
   (-1, "Yes")
)

OPEN_PUBLICATION=(
   ("", "Not specified"),
   ("n", "No"),
   ("y", "Yes")
)
