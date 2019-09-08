import os, sys, subprocess

def eml2pst(src=None, dst=None):
    if src and dst:
        print('\nConverting EML files in {}'.format(os.path.abspath(src)))
        subprocess.call(
            '"{3}" /u OutlookConvertEML2PST SourceDir={0} TargetFile={1}\{2}.pst Subfolders=False Folder=Inbox'.format(
                src, dst, os.path.basename(src), reliefjet_path))
        print('Saved PST file in {}'.format(dst))
        input('\nPress any key to exit.')

    elif dst and not src:
        src_dirs = os.getcwd()
        for src in os.listdir(src_dirs):
            if os.path.isdir(src):
                if any(file.endswith('.eml') for file in os.listdir(src)):
                    print('\nConverting EML files in {}'.format(os.path.abspath(src)))
                    subprocess.call(
                        '"{3}" /u OutlookConvertEML2PST SourceDir={0} TargetFile={1}\{2}.pst Subfolders=False Folder=Inbox'.format(
                          src, dst, os.path.basename(src), reliefjet_path))
                    print('Saved PST file in {}'.format(dst))
        input('\nPress any key to exit.')

    elif src and not dst:
        if not os.path.exists('{}\PST'.format(os.getcwd())):
            os.mkdir('PST')
        dst = '{}\PST'.format(os.getcwd())
        print('\nConverting EML files in {}'.format(os.path.abspath(src)))
        subprocess.call(
            '"{3}" /u OutlookConvertEML2PST SourceDir={0} TargetFile={1}\{2}.pst Subfolders=False Folder=Inbox'.format(
                src, dst, os.path.basename(src), reliefjet_path))
        print('Saved PST file in {}'.format(dst))
        input('\nPress any key to exit.')

    else:
        src_dirs = os.getcwd()
        if not os.path.exists('{}\PST'.format(os.getcwd())):
            os.mkdir('PST')
        dst = '{}\PST'.format(os.getcwd())
        for src in os.listdir(src_dirs):
            if os.path.isdir(src):
                if any(file.endswith('.eml') for file in os.listdir(src)):
                    print('\nConverting EML files in {}'.format(os.path.abspath(src)))
                    subprocess.call(
                        '"{3}" /u OutlookConvertEML2PST SourceDir={0} TargetFile={1}\{2}.pst Subfolders=False Folder=Inbox'.format(
                          src, dst, os.path.basename(src), reliefjet_path))
                    print('Saved PST file in {}'.format(dst))
        input('\nPress any key to exit.')

def get_path():
    src = input('Enter a directory path with eml files [or leave it blank to convert folders \nin the current directory]:')
    if src != "":
        while not os.path.exists(src):
            print('{} does not exist'.format(src))
            src = input( 'Please enter a valid path [or leave it blank and press [ENTER] to convert folders \nin the current directory]: ')

    dst = input('Enter a directory path to store the converted PST files in [or leave it black to\n save it in current directory]: ')
    if dst != "":
        if not os.path.exists(dst):
            path = input('{} does not exist, Do you want to create it? [Y/N]: '.format(dst))
            if path.lower() == 'yes' or path.lower() == 'y':
                os.mkdir(dst)
            if path.lower() == 'no' or path.lower() == 'n':
                print('Exiting..')
                sys.exit(1)

    return src, dst

def main():
    print('==============================')
    print('==== EML to PST Converter ====')
    print('==============================\n\n')
    src, dst = get_path()
    eml2pst(src, dst)


if __name__ == '__main__':
    reliefjet_path = "C:\\Program Files (x86)\\ReliefJet Essentials\\ExecutorCli.exe"
    if not os.path.exists(reliefjet_path):
        print('Looks like ReliefJet Essentials is not installed, Install it and try again.\n')
        input('Press any key to exit.')
        sys.exit(1)
    else:
        main()

