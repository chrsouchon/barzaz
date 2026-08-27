import os

def main():
    # list of file extensions to track (video files)
    file_extension_list = [".mp4", ".mov", ".avi", ".mkv", ".wmv", ".flv", ".webm", ".vob", ".ogg", ".ogv", ".gifv", ".qt", ".swf", ".avchd", ".m4v", ".3gp", ".3g2", ".mxf", ".roq", ".nsv", ".f4v", ".f4p", ".f4a", ".f4b", ".m2ts", ".ts", ".m2v", ".m4v", ".m2p", ".m2t", ".m2ts", ".mts", ".m1v", ".m1a", ".m2a", ".m4a", ".m4p", ".m4b", ".m4r", ".m4z", ".mka", ".mk3d", ".mkv"]

    file_path = os.getcwd()

    command = ""
    # for loop that makes the command "git lfs track" for each file extension
    for file_extension in file_extension_list:
        command = "git lfs track " + "*" + file_extension
        os.system(command)

    return file_extension_list

if __name__ == "__main__":
    main()