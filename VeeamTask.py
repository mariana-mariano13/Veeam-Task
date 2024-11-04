import os
import shutil
import time
import argparse
import logging
import hashlib

"""
Purpose: Configure the logging system - both file and console
Input Parameters:
    log_file (str) - Log File Path;
Output Parameters:
Notes:
    Configures the logging system by:
        Creating and configuring the logger; 
        Setting the logging level; 
        Adding handlers to both a file and the console; 
        Specifying a format for log messages;
Prints:
"""
def setup_logging(log_file):
   
    logger = logging.getLogger() # Create or get the root logger
    logger.setLevel(logging.INFO) # Set the logging level to INFO for the logger

    file_handler = logging.FileHandler(log_file) # Create a file handler
    file_handler.setLevel(logging.INFO) # Set the logging level to INFO 

    console_handler = logging.StreamHandler() # Create a console handler
    console_handler.setLevel(logging.INFO) # Set the logging level

    formatter = logging.Formatter('%(asctime)s : %(levelname)s - %(message)s') # Define the log message format
    # Set the formatter for the file and console handler
    file_handler.setFormatter(formatter) 
    console_handler.setFormatter(formatter)
    #Add the file and console handler to the logger
    logger.addHandler(file_handler) 
    logger.addHandler(console_handler)


"""
Purpose: Calculate the MD5 hash of a file. 
Input Parameters:
    file (str) - File Path;
Output Parameters:
    str - MD5 hash of the input file as a hexadecimal
Notes:
    Open in binary mode the input file
    Read in chunks of 4096 bytes to handle large files efficiently.
    The MD5 hash is updated incrementally with each chunk read.
    The resulting hash is returned as a hexadecimal string.
Prints:
Based on: https://www.geeksforgeeks.org/finding-md5-of-files-recursively-in-directory-in-python/
"""
def calculate_md5(file):
    hash_md5 = hashlib.md5()

    with open(file, "rb") as f:

        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)

    return hash_md5.hexdigest()


"""
Purpose: Calculate the MD5 hash of the contents of a folder.
Input Parameters:
    folder (str) - Folder Path;
Output Parameters:
    str - MD5 hash of the input folder as a hexadecimal
Notes:
    Includes the files and subfolders
    Considers the structure of files and subfolders.
Prints:
"""
def calculate_folder_md5(folder):
    md5_hash = hashlib.md5()

    for dirpath, dirnames, filenames in os.walk(folder): # Walk through the directory
        dirnames.sort()
        filenames.sort()

        for filename in filenames: # Iterate every file
            file_path = os.path.join(dirpath, filename) # Path of the file
            file_md5 = calculate_md5(file_path)

            relative_path = os.path.relpath(file_path, folder) # Have in consideration the strucuture of the files and subfolders

            md5_hash.update(relative_path.encode('utf-8'))
            md5_hash.update(file_md5.encode('utf-8')) 

    return md5_hash.hexdigest()


"""
Purpose: Copy all files and folders that do not exist or have been updated from the source to the replica 
Input Parameters:
    source (str) - Source Path;
    replica (str) - Replica Path;
Output Parameters:
Notes:
    It takes in consideration:
        if the file or folder already exist 
        if the file exists in the replica verifies if the source one has been updated
Prints:
    Copied file: 'item name' - 'source path' to 'replica path' - Everytime a file is copied and it did not previously exist in the replica folder
    Copied the latest version of the file: 'item name' - 'source path' to 'replica path' - Everytime a file is overwritten in the replica folder
"""
def copy_files(source, replica):

    for item in os.listdir(source): # Iterate over each item in the source
        source_path = os.path.join(source, item)
        replica_path = os.path.join(replica, item)

        if os.path.isfile(source_path):  # In case of a file
            if not os.path.exists(replica_path): # If a file exists in the replica
                shutil.copy2(source_path, replica_path)
                logging.info(f'Copied file: {item} - {source_path} to {replica_path}')
            
            elif os.path.getmtime(source_path) > os.path.getmtime(replica_path):
                if calculate_md5(source_path) != calculate_md5(replica_path): # If a file has been updated in the source
                    shutil.copy2(source_path, replica_path) # Overwrites the existing file
                    logging.info(f'Copied the latest version of the file: {item} - {source_path} to {replica_path}')
       
        elif os.path.isdir(source_path): # In case of a folder
            sync_folders(source_path, replica_path)


"""
Purpose: Remove all the files in the replica folder that do not exist in the source foulder
Input Parameters:
    source (string) - Source Path;
    replica (string) - Replica Path;
Output Parameters:
Notes:
Prints:
    Removed folder 'item name' with the path 'replica path' - Everytime a folder is removed shows its name
    Removed file 'item name' with the path 'replica path' -  Everytime a file is removed shows its name
"""
def remove_files(source, replica):
    
    for item in os.listdir(replica): # Iterate over each item in the replica folder
        replica_path = os.path.join(replica, item)
        source_path = os.path.join(source, item)

        if not os.path.exists(source_path): # If a file doesnt exist in the source
            if os.path.isdir(replica_path): # In case of a folder
                shutil.rmtree(replica_path)
                logging.info(f'Removed folder {item} with the path {replica_path}')

            else: # In case of a file
                os.remove(replica_path)
                logging.info(f'Removed file {item} with the path {replica_path}')


"""
Purpose: Synchronizes the content of the replica folder to a source folder 
Input Parameters:
    source (string) - Source Path;
    replica (string) - Replica Path;
Output Parameters:
Notes:
    Synchronizes 2 folders by:
        Verifing if a replica folder already exists and if not creates it;
        Verify if the source folder was updated or not;
        If it was:
            Copying all folders and files from source to replica;
            Removing all folders and files from replica that don't exist in the source;
Prints:
    Creating folder with the path: 'replica path' - Eveytime a folder doesnt exist and needs to be created, including the replica folder and all subfolders
    No updates needed on the folder with the path: 'replica path' - Everytime a folder already exists in the replica folder and is already updated
    Sync folder: 'replica path' - Everytime a folder begins the sync process (replica or subfolder)
"""
def sync_folders(source, replica):
    if not os.path.exists(replica): # In case the file doesnt exists
        os.makedirs(replica)
        logging.info(f'Creating folder with the path: {replica}')

    if os.path.getmtime(source) <= os.path.getmtime(replica):
        md5_source = calculate_folder_md5(source)
        md5_replica = calculate_folder_md5(replica)
        if md5_source == md5_replica: # In case the folder and its items have been updated in the source
            logging.info(f'No updates needed on the folder: {replica}')
            return
    
    logging.info(f'Sync folder: {replica}')
    copy_files(source, replica)
    remove_files(source, replica)


"""
Purpose:
Input Parameters:
Output Parameters:
Notes:  
    Manages the input parameters;
    Sets up logging;
    Initiates the periodic process for synchronization of the folders;
    Error handling;
Prints:
    Starting synchronization... - Everytime the process of synchronization starts
    Synchronization completed. - Everytime the process of synchronization ends
    File not found error: 'file path' - Everytime a file not found error occurs
    Permission error: 'file path' - Everytime an access file or folder issue error occurs
    An exception error: 'file path' - Everytime an exception occurs
"""
def main():
    parser = argparse.ArgumentParser(description='Synchronize 2 folders (Source -> Replica).')
    parser.add_argument('source', help='Source folder path (Existing)')
    parser.add_argument('replica', help='Replica folder path (Existing or Nonexistent)')
    parser.add_argument('sync_interval', type=int, help='Synchronization interval (s)')
    parser.add_argument('log_file', help='Log file path (Existing or Nonexistent)')

    args = parser.parse_args()

    setup_logging(args.log_file)

    while True:
        try:
            logging.info('Starting synchronization...')
            sync_folders(args.source, args.replica)
            logging.info('Synchronization completed.')
        except FileNotFoundError as e:
            logging.error(f'File not found error: {e}')
        except PermissionError as e:
            logging.error(f'Permission error: {e}')
        except Exception as e:
            logging.error(f'An exception error: {e}')
        finally:
            # Waiting for the next process of sync
            time.sleep(args.sync_interval)

if __name__ == '__main__':
    main()
