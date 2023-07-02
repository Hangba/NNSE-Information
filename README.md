# NNSE-Information
This is a tool to view the registeration data of Nanning High School conveniently with GUI. It was first come out in July, 2021.

### Dependencies
* openpyxl
* pythonping
* pyqt5
* pillow
* matplotlib (future)

### How to Use
Each time you use the software you need to click on the Initialise button to initialise it, then select whether you want the data for general or vocational education and click on 'Get Current Information' to get the current data from the API available at www.nnzkzs.com. Once the data has been retrieved the program will automatically open the saved zip file, or use the Open option in the menu to open the local zip file, select the school and the data for each school will be displayed in the List control. You can also use the loop function on the right hand side of the UI to get the current data at regular intervals, the files are saved in the saves folder by default.
![250350479-d346d4c5-9129-49e5-b4d7-c1e0bc568912](https://github.com/Hangba/NNSE-Information/assets/36891442/7830e994-1b22-43b7-8468-9f297a9a114f)
![{F1571B47-3781-44d9-AC64-E2BB3F2BA86E}](https://github.com/Hangba/NNSE-Information/assets/36891442/feb72a0a-cc71-47ba-9957-97fa7414b1f6)

### Future Plans
* Optimising data output
* Visualising data using matplotlib
* Adding the data process function for a sequence of datas

# NNSE-Information
这是一个用于获取、显示中考数据的带UI的工具，最初版在2021年7月发布。

### 依赖
* openpyxl
* pythonping
* pyqt5
* pillow
* matplotlib （未来）

### 如何使用
每次使用软件时需要点击初始化按钮初始化，然后选择要普高还是职高的数据，点击“Get Current Information”从 www.nnzkzs.com 公开的API获取当前数据。获取完数据后程序会自动打开保存好的zip文件，使用菜单里的Open选项也可以打开本地zip文件，选择学校，各个学校的数据会显示在List控件中。另外可以使用UI右侧的循环功能定时获取当前数据，文件默认保存在saves文件夹。

### Future Plans
* 优化数据输出
* 使用matplotlib进行数据可视化
* 添加对一系列数据的处理功能


