/*
*  Simple wrapper around 'pan_df' command that allows users to find the amount of space
*  used on panasus storage even if they do not have the appropiate file permissions. The 
*  executable generated from compiling this program should be run as a setuid script as user 
* 'root':
*
*  ls -l pan_df_root
*
*   -rwsr-xr-x 1 root root 6515 Jan 13 13:53 pan_df
*
* History:
*
*     31-Mar-2006 Badly written by ASH
*/

#include <stdio.h>
#include <unistd.h>

main (int argc, char *argv[]) {

   int ret;

   ret = execl ("/usr/local/bin/pan_df", "-k", argv[1]);
   return (ret);

}
