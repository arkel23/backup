#!/usr/bin/env python3
from __future__ import print_function
import os
import io
import time
from os.path import join

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from httplib2 import Http
from oauth2client import file, client, tools

import argparse, os, sys, path, platform, datetime
import shutil
import subprocess
from subprocess import Popen, PIPE
from os.path import expanduser
home = expanduser("~")

FOLDER_AUX = 'aux_files'
# Authority
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']


def delete_drive_service_file(service, file_id):
    service.files().delete(fileId=file_id).execute()


def update_file(service, update_drive_service_name, local_file_path, update_drive_service_folder_id):
    print("uploading...")
    if update_drive_service_folder_id is None:
        file_metadata = {'name': update_drive_service_name}
    else:
        print("folder's id on gdrive: %s" % update_drive_service_folder_id)
        file_metadata = {'name': update_drive_service_name,
                         'parents': update_drive_service_folder_id}

    media = MediaFileUpload(local_file_path, )
    file_metadata_size = media.size()
    start = time.time()
    file_id = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
    end = time.time()
    print("uploading successful!")
    print('filename on gdrive: ' + str(file_metadata['name']))
    print('Files ID: ' + str(file_id['id']))
    print('size of file : ' + str(file_metadata_size) + ' byte')
    print("time of uploading: " + str(end-start))

    return file_metadata['name'], file_id['id']


def search_folder(service, update_drive_folder_name=None):
    get_folder_id_list = []
    print(len(get_folder_id_list))
    if update_drive_folder_name is not None:
        response = service.files().list(fields="nextPageToken, files(id, name)", spaces='drive',
                                       q = "name = '" + update_drive_folder_name + "' and mimeType = 'application/vnd.google-apps.folder' and trashed = false").execute()
        for file in response.get('files', []):
            # Process change
            print('Found file: %s (%s)' % (file.get('name'), file.get('id')))
            get_folder_id_list.append(file.get('id'))
        if len(get_folder_id_list) == 0:
            print("There is no this folder's name on your google drive. so it will be upload under /.. ")
            return None
        else:
            return get_folder_id_list
    return None


def search_file(service, update_drive_service_name, is_delete_search_file=False):

    # Call the Drive v3 API
    results = service.files().list(fields="nextPageToken, files(id, name)", spaces='drive',
                                   q="name = '" + update_drive_service_name + "' and trashed = false",
                                   ).execute()
    items = results.get('files', [])
    if not items:
        print('Fail to find your : ' + update_drive_service_name + ' File .')
    else:
        print('Search File: ')
        for item in items:
            times = 1
            print(u'{0} ({1})'.format(item['name'], item['id']))
            if is_delete_search_file is True:
                print("Deleted file : " + u'{0} ({1})'.format(item['name'], item['id']))
                delete_drive_service_file(service, file_id=item['id'])

            if times == len(items):
                return item['id']
            else:
                times += 1


def trashed_file(service, is_delete_trashed_file=False):
    results = service.files().list(fields="nextPageToken, files(id, name)", spaces='drive', q="trashed = true",
                                   ).execute()
    items = results.get('files', [])
    if not items:
        print('no file in trash can.')
    else:
        print('file in trash can : ')
        for item in items:
            print(u'{0} ({1})'.format(item['name'], item['id']))
            if is_delete_trashed_file is True:
                print("deleted file :" + u'{0} ({1})'.format(item['name'], item['id']))
                delete_drive_service_file(service, file_id=item['id'])


def get_update_files_path_list(update_files_path):


    UploadFilesPathList = []
    UploadFilesNameList = []
    for root, dirs, files in os.walk(update_files_path):
        for f in files:
            fullPath = join(root, f)
            UploadFilesPathList.append(fullPath)
            UploadFilesNameList.append(f)
    print("get the file ready to upload on gdrive \n%s" % '\n'.join(UploadFilesPathList))
    return UploadFilesNameList, UploadFilesPathList


def main_og(is_update_file_function=False, update_drive_service_folder_name=None, update_drive_service_name=None, update_file_path=None, log_backup_auto=None, curr_time=None):



    print("is_update_file_function: %s" % is_update_file_function)
    print("update_drive_service_folder_name: %s" % update_drive_service_folder_name)

    store = file.Storage(os.path.join(FOLDER_AUX,'token.json'))
    creds = store.get()
    if not creds or creds.invalid:
        flow = client.flow_from_clientsecrets(os.path.join(FOLDER_AUX, 'credentials.json'), SCOPES)
        creds = tools.run_flow(flow, store)
    service = build('drive', 'v3', http=creds.authorize(Http()))
    print('*' * 10)

    if is_update_file_function is True:

        if update_drive_service_name is None:  
            print("Uploading all file in your folder")
            UploadFilesName, UploadFilesPath = get_update_files_path_list(update_files_path = update_file_path)
            print("=====Uploading...=====")
            get_folder_id = search_folder(service = service, update_drive_folder_name = update_drive_service_folder_name)
            print(UploadFilesPath)
            for UploadFileName in UploadFilesName:
                search_file(service = service, update_drive_service_name = UploadFileName, is_delete_search_file = True)
            for i in range(len(UploadFilesPath)):
                file_name, file_id = update_file(service=service, update_drive_service_name=UploadFilesName[i],
                            local_file_path=UploadFilesPath[i], update_drive_service_folder_id=get_folder_id)
                log_msg = str('filename: ' + str(file_name) + '_ id: ' + file_id + '\n')
                log_backup_auto.write(curr_time + '\t' + log_msg)
            print("=====Uploading Finish=====")

        else:  
            print(update_file_path + update_drive_service_name)
            print("=====Uploading files=====")
            get_folder_id = search_folder(service = service, update_drive_folder_name = update_drive_service_folder_name)
           
            search_file(service=service, update_drive_service_name=update_drive_service_name, is_delete_search_file=True)
           
            update_file(service=service, update_drive_service_name=update_drive_service_name,
                        local_file_path=update_file_path + update_drive_service_name, update_drive_service_folder_id=get_folder_id)
            print("=====Uploading done =====")

def add_folders(path_tracker):
    #prompt user for adding paths

    while True:
        inp = input('Please copy full path to folder. Leave empty to continue: ')
        if inp=='':
            break
        else:
            if (os.path.exists(os.path.normpath(inp))):
                path_tracker.write(os.path.abspath(inp))
                path_tracker.write('\n')
            else:
                print('Directory not valid. Please add a correct directory.')

def compress_folder(curline, log_backup_auto, curr_time):
    # compress the contents of each folder and return a compressed file
    curline = os.path.normpath(curline.strip('\n'))
    filename = os.path.join('compressed', os.path.basename(os.path.normpath(curline)))
    shutil.make_archive(filename, 'tar', curline)
    

def task_scheduler_win(path_exe, path_curr, time_run1, time_run2):
    # makes a task schedule script which runs on fixed times

    #syntax: /CREATE /SC [MINUTE/HOURLY/DAILY/WEEKLY/MONTHLY/
    # ONCE/ONSTART/ONLOGON/ONIDLE/ONEVENT] /D [MON to SUN or 1-31 or *]
    # /TN [TASK NAME AND LOCATION] /TR [LOCATION AND NAME OF TASK TO RUN]
    # /ST [TIME TO TRUN TASK (24 HOURS FORMAT)]

    bat_name = 'task_scheduler.bat'
    task_scheduler = open(os.path.join(FOLDER_AUX, bat_name), 'w')
    print(path_exe)
    print(path_curr)
    task_scheduler.write('''SCHTASKS /CREATE /SC DAILY /TN "backup_auto_1" /TR "{} {}" /ST {}:00\n'''.format(path_exe, path_curr, time_run1))
    task_scheduler.write('''SCHTASKS /CREATE /SC DAILY /TN "backup_auto_2" /TR "{} {}" /ST {}:00'''.format(path_exe, path_curr, time_run2))
    task_scheduler.close()

    r_c = run_subprocess(os.path.join(FOLDER_AUX, bat_name))
    
    return r_c

def task_scheduler_linux(path_exe, path_curr, time_run1, time_run2):
    # makes a task schedule script which runs on fixed times
    pass

def run_subprocess(cmd, curr_os='Windows', commit=False, curr_date=0, stdout=False):

    if (commit == False):
        if (curr_os != 'Windows'):
            cmd = cmd.split(' ')
            cmd = [word.replace(' ','') for word in cmd]
    else:
        cmd = ['git', 'commit', '-m', '"AutomaticCommitDoneAt_{}"'.format(curr_date)]

    if (stdout == True):
        p = Popen(cmd, stdout = subprocess.PIPE, stderr = subprocess.PIPE,)
        stdout, stderr = p.communicate()
        return p.returncode, stdout
    else:
        p = Popen(cmd)
        stdout, stderr = p.communicate()
        return p.returncode

def initialize(curr_time, curr_os):
    log_backup_auto = open(os.path.join(FOLDER_AUX,'log_backup_auto.txt'), 'w')
    log_backup_auto.write('curr_time\tlog_msg\n')

    path_tracker = open(os.path.join(FOLDER_AUX,'path_tracker.txt'), 'w')
    path_tracker.write('#local_repo_path\n')

    time_run1 = input('Fixed time 1 to run script(number from 01-23): ')
    time_run2 = input('Fixed time 2 to run script(number from 01-23): ')

    try:
        exe = sys.executable #python executabe path
        path_exe = path.Path(exe)  #path for the exe
        path_curr = path.Path(os.getcwd()) #path for curr directory
        script_name = os.path.basename(__file__)
        path_curr = os.path.join(path_curr, script_name)
    except:
        log_msg = 'Error in either executable or current path. Closing prematurely.'
        log_backup_auto.write(curr_time + '\t' + log_msg)
        log_backup_auto.close()
        path_tracker.close()

    print('OS:', curr_os)
    if (curr_os == 'Windows'):
        rc = task_scheduler_win(path_exe, path_curr, time_run1, time_run2)
        log_msg = 'Return code for initializing task_scheduler_win: {}\n'.format(rc)
        log_backup_auto.write(curr_time + '\t' + log_msg)
    elif (curr_os == 'Linux'):
        task_scheduler_linux(path_exe, path_curr, time_run1, time_run2)
        log_msg = 'No task scheduler for this platform. Manual operation only.\n'
        log_backup_auto.write(curr_time + '\t' + log_msg)
    else:
        log_msg = 'No task scheduler for this platform. Manual operation only.\n'
        log_backup_auto.write(curr_time + '\t' + log_msg)

    add_folders(path_tracker)
    path_tracker.close()

    log_msg = 'Initialized path_tracker.txt file\n'
    log_backup_auto.write(curr_time + '\t' + log_msg)
        
    return log_backup_auto

def check_setup(ft):
    print('First time setup: ', ft)
    curr_time = str(datetime.datetime.now()).replace(' ','_').replace(':','-')
    curr_time = curr_time.split('.', 1)[0]
    curr_os = platform.system()
    
    os.makedirs(FOLDER_AUX, exist_ok=True)

    #initializes log, path tracker and scheduler if first time, else runs updating
    if ft:
        log_backup_auto = initialize(curr_time, curr_os) 
    else:
        log_backup_auto = open(os.path.join(FOLDER_AUX,'log_backup_auto.txt'), 'a')
    
    path_tracker = open(os.path.join(FOLDER_AUX,'path_tracker.txt'), 'r')
    
    for curline in path_tracker:
        if not curline.startswith('#'):
            compress_folder(curline, log_backup_auto, curr_time)
    
    main_og(is_update_file_function=bool(True), 
            update_drive_service_folder_name='BACKUPS',
            update_drive_service_name=None, 
            update_file_path=os.path.join(os.getcwd(), 'compressed')
            ,log_backup_auto=log_backup_auto, curr_time=curr_time)


    path_tracker.close()
    log_backup_auto.close()
    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-ft', required=False, 
    dest='ft', type=str, default=False,
    help='''Tells script if needs to do initial setup (first time). Default is False.\n
    If first time please run with flag: -init True which will make it run initial setup.
    If False then runs update routine.''')
    
    args = parser.parse_args()

    if (args.ft == 'True'):
        init_setup = True
        check_setup(ft=init_setup)
    else:
        init_setup = False
        check_setup(ft=init_setup)

main()