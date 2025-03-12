#!/bin/bash

#############################
#  ml-config-hash.sh
#  Version: 0.7
##############################
#  Author: Mike Gardner, 
#			Staff Engineer, MarkLogic
#  Purpose:
#    This script is intended for monitoring changes
#  to database configuration, library and binary files.
####
#  Description:
#    This script will generate an md5 checksum on the contents of the 
#  MarkLogic configuration files in /var/opt/MarkLogic, the MarkLogic binaries
#  in /opt/MarkLogic/bin and the MakLogic libraries in /opt/MarkLogic/lib.
#  Checksum values are compared to the previous occurance (if it exists).
#  For automated monitoring, this should be setup as a cron job.  
####
#  To use:  
#     Update EMAIL_LIST with emails for users that should be notified of the
#  results.
#     By default, the script emails reports in case of a pass, a failure or
#  when an existing baseline checksum file is not found, and a new baseline 
#  checksum file is generated.  To turn off pass notifications, change the
#  the value of EMAIL_PASS to 0.
####
#  Requirements:
#  Read access to contents of /var/opt/MarkLogic & /opt/MarkLogic
#############################

# EMAIL_LIST should be comma separated list of emails to send results to
EMAIL_LIST="admin@server.location.mil"
MARKLOGIC_HOME="/var/opt/MarkLogic"
ML_BIN="/opt/MarkLogic/bin"
ML_LIB="/opt/MarkLogic/lib"
OUTPUT_DIR="/var/local"
PREVIOUS_HASH="baseline-md5.hashes"
EMAIL_PASS=1
EMAIL_FAIL=1
VERBOSE=0
TMP_DIR="/tmp"


hashFile="baseline-md5.hashes"
#tempFile="md5-hash-report.$$"
reset=false
localDate=`date`
# Check arguments
if [[ $# -gt 0 ]]; then
	if [[ $* = *reset* ]];then
		reset="true"
	elif [[ $* = *verbose* ]]; then
		verbose="true"
	else
		printf '\n%s\n' "Usage: $0 [reset] [verbose] [help]"
		printf '%s\n' 'Options:'
		printf '\t%s\n' "reset:     Resets md5 hash file to current configurations"
		printf '\t%s\n' "verbose:   Prints generated report to stdout, and will not send email report"
		printf '\t%s\n\n' "help:      Prints this usage message"
		exit 0
	fi
fi

configFiles="$MARKLOGIC_HOME/server.xml \
	$MARKLOGIC_HOME/hosts.xml \
	$MARKLOGIC_HOME/clusters.xml 
	$MARKLOGIC_HOME/groups.xml \
	$MARKLOGIC_HOME/assignments.xml \
	$MARKLOGIC_HOME/keystore.xml \
	$MARKLOGIC_HOME/hsm.cfg \
	$MARKLOGIC_HOME/Label"

binFiles=`ls -d $ML_BIN/*`

libFiles=`ls -d $ML_LIB/*`

if [ $reset = "true" ]; then
	printf '\n%s\n\n' 'Reseting md5 checksums'
	md5sum $configFiles > ${OUTPUT_DIR}/baseline-md5.hashes
	exit 0
fi

#printf "\n"
reportOutput=
hashResults=""
changeDetected=0
count=1
nl=$'\n'

# If previous hash exists, do the hash comparison
#  else create the baseline hash file
if [ -f "$OUTPUT_DIR/$PREVIOUS_HASH" ]; then
	#printf '\n%s\n' 'Comparing against baseline' >> $tempFile
	reportOutput+="${nl}Comparing against baseline:  "
	hashResults=`/usr/bin/md5sum --check ${OUTPUT_DIR}/baseline-md5.hashes`
else
	reportOutput+="${nl}No Previous Baseline Found. Creating Baseline Hashes.${nl}"
	md5sum $configFiles $binFiles $libFiles> ${OUTPUT_DIR}/baseline-md5.hashes
fi

# If the comparison fails, set changeDetected flag to 1
#  or if a new baseline file is created set changeDetected flag to 1
#  else set change detected flag to 0
if [[ $hashResults = *FAILED* ]]; then
	reportOutput+="Change Detected, Review Output for Details${nl}"
	reportOutput+=$hashResults
	reportOutput+="${nl}${nl}Create a new basline hash after verifying change by removing $OUTPUT_DIR/$PREVIOUS_HASH${nl}"
	changeDetected=1
elif [[ $hashResults = "" ]]; then
	reportOutput+="New Baseline Created: Review Output for Details${nl}"
	changeDetected=1
else
	reportOutput+="No Changes Detected${nl}"
	reportOutput+=$hashResults
	changeDetected=0
fi

# Print report to CLI if verbose in $1
#  and sets email generation to false
if [[ $verbose = "true" ]];then
	printf '%s\n\n' "$reportOutput"
	EMAIL_FAIL=0
	EMAIL_PASS=0
fi
# If Change was detected, and EMAIL_FAIL=1, then send email
#  else if change was not detected and EMAIL_PASS=1, also send email
if [[ $changeDetected -eq 1 ]] && [[ $EMAIL_FAIL -eq 1 ]]; then
	printf '%s\n' "$reportOutput" | mail -s "MarkLogic **Configuration Change Detected** $localDate" $EMAIL_LIST
elif [[ $changeDetected -eq 0 ]] && [[ $EMAIL_PASS -eq 1 ]]; then
	printf '%s\n' "$reportOutput" | mail -s "MarkLogic Configuration No Change Detected $localDate" $EMAIL_LIST
fi


#cat $tempFile; rm -r $tempFile

#printf $reportOutput
# if [[ $changeDetected=0 ]]
# 	printf "\nNo Change Detected\n"