import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/wolfwagen/Undergrad_Minchan_Folder/ROOMBA_PROJECT_1/install/first_roomba_pkg'
