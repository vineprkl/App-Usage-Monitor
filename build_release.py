import os
import shutil
import zipfile
from datetime import datetime

def create_release():
    """创建发布包"""
    # 版本信息
    version = "1.0.0"
    release_date = datetime.now().strftime("%Y%m%d")
    
    # 创建发布目录
    release_dir = f"app_usage_monitor_v{version}"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 需要复制的文件列表
    files_to_copy = [
        'start.bat',
        'start.py',
        'app.py',
        'control_panel.py',
        'config.py',
        'requirements.txt',
        'README.md',
        'RELEASE.md'
    ]
    
    # 复制主程序文件
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, release_dir)
            print(f"已复制: {file}")
    
    # 复制templates目录
    templates_dir = os.path.join(release_dir, 'templates')
    if os.path.exists('templates'):
        shutil.copytree('templates', templates_dir)
        print("已复制: templates目录")
    
    # 创建zip文件
    zip_filename = f"app_usage_monitor_v{version}_{release_date}.zip"
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(release_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, release_dir)
                zipf.write(file_path, arcname)
    
    print(f"\n发布包创建成功：{zip_filename}")
    
    # 清理临时目录
    shutil.rmtree(release_dir)
    print("临时文件已清理")

if __name__ == '__main__':
    print("开始创建发布包...")
    create_release()
    print("\n发布包创建完成！") 