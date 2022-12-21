'''
俄罗斯方块
pyrcc5 -o resource.py resource.qrc
pyinstaller -w -i a.ico Tetris_game.py
'''
import math, resource
import ctypes
ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("myappid")

from PyQt5.QtWidgets import QMainWindow, QFrame, QDesktopWidget, QApplication, QPushButton, QVBoxLayout
from PyQt5.QtCore import Qt, QBasicTimer, pyqtSignal
from PyQt5.QtGui import QPainter, QColor, QIcon
import sys, random

class Tetris(QMainWindow):

    def __init__(self):
        super().__init__()

        self.initUI()


    def initUI(self):
        '''initiates application UI'''
        # 创建了一个Board类的实例，并设置为应用的中心组件
        self.tboard = Board(self)
        self.setCentralWidget(self.tboard)
        # 创建一个statusbar来显示三种信息：消除的行数，游戏暂停状态或者游戏结束状态
        # msg2Statusbar是一个自定义的信号，用在（和）Board类（交互），showMessage()方法是一个内建的，用来在statusbar上显示信息的方法。
        self.statusbar = self.statusBar()
        self.tboard.msg2Statusbar[str].connect(self.statusbar.showMessage)

        self.tboard.start() # 初始化游戏

        # self.btn = QPushButton("开始游戏", self)
        # self.btn.clicked[bool].connect(self.start)
        #
        # vbox = QVBoxLayout(self)
        # vbox.addWidget(self.btn)
        # vbox.addWidget(self.tboard)
        #
        # self.setLayout(vbox)

        self.resize(213, 426)   #  设置窗口大小
        # self.setGeometry(300, 300, 500, 300)
        self.center()   # 窗口居中
        self.setWindowTitle('Tetris')   # 标题
        self.setWindowIcon(QIcon(':/a.ico'))
        self.show() # 展示窗口


    def center(self):
        '''centers the window on the screen'''
        # screenGeometry（）函数提供有关可用屏幕几何的信息
        screen = QDesktopWidget().screenGeometry()
        # 获取窗口坐标系
        size = self.geometry()
        # 将窗口放到中间
        self.move((screen.width()-size.width())//2,
            (screen.height()-size.height())//2)

class Board(QFrame):
    # 创建了一个自定义信号msg2Statusbar，当我们想往statusbar里显示信息的时候，发出这个信号就行了。
    msg2Statusbar = pyqtSignal(str)
    # 这些是Board类的变量。BoardWidth和BoardHeight分别是board的宽度和高度。Speed是游戏的速度，每300ms出现一个新的方块
    BoardWidth = 10 # 指界面宽度可以容纳10个小方块
    BoardHeight = 22    # 指界面高度可以容纳22个小方块
    Speed = 300

    def __init__(self, parent):
        super().__init__(parent)

        self.initBoard()


    def initBoard(self):
        '''initiates board'''

        self.timer = QBasicTimer()  # 定义了一个定时器
        self.isWaitingAfterLine = False # self.isWaitingAfterLine表示是否在等待消除行

        self.curX = 0   # 目前x坐标
        self.curY = 0   # 目前y坐标
        self.numLinesRemoved = 0    # 表示消除的行数，也就是分数
        self.board = [] # 存储每个方块位置的形状，默认应该为0，下标代表方块坐标x*y

        self.setFocusPolicy(Qt.StrongFocus) # 设置焦点，使用tab键和鼠标左键都可以获取焦点
        self.isStarted = False  # 表示游戏是否在运行状态
        self.isPaused = False   # 表示游戏是否在暂停状态
        self.clearBoard()   # 清空界面的全部方块

    # shapeAt()决定了board里方块的的种类。
    def shapeAt(self, x, y):
        '''determines shape at the board position'''
        # 返回的是（x,y)坐标方块在self.board中的值
        return self.board[(y * Board.BoardWidth) + x]


    def setShapeAt(self, x, y, shape):
        '''sets a shape at the board'''
        # 设置方块的形状，放入self.board中
        self.board[(y * Board.BoardWidth) + x] = shape

    # board的大小可以动态的改变。所以方格的大小也应该随之变化。squareWidth()计算并返回每个块应该占用多少像素--也即Board.BoardWidth。
    def squareWidth(self):
        '''returns the width of one square'''

        return self.contentsRect().width() // Board.BoardWidth


    def squareHeight(self):
        return self.contentsRect().height() // Board.BoardHeight

    # 开始游戏
    def start(self):
        '''starts game'''
        # 如果游戏处于暂停状态，直接返回
        if self.isPaused:
            return

        self.isStarted = True   # 将开始状态设置为True
        self.isWaitingAfterLine = False
        self.numLinesRemoved = 0    # 将分数设置为0
        self.clearBoard()   # 清空界面全部的方块
        # 状态栏显示当前有多少分
        self.msg2Statusbar.emit(str(self.numLinesRemoved))
        print("start game")

        self.newPiece() # 创建一个新的方块
        self.timer.start(Board.Speed, self) # 开始计时，每过300ms刷新一次当前的界面

    # pause()方法用来暂停游戏，停止计时并在statusbar上显示一条信息
    def pause(self):
        '''pauses game'''
        # 如果有处于运行状态，则直接返回
        if not self.isStarted:
            return
        # 更改游戏的状态
        self.isPaused = not self.isPaused

        if self.isPaused:
            self.timer.stop()   # 停止计时
            self.msg2Statusbar.emit(f"paused, current socre is {self.numLinesRemoved}")   # 发送暂停信号,同时显示当前分数
            print(f"paused, current socre is {self.numLinesRemoved}")
        # 否则继续运行，显示分数
        else:
            self.timer.start(Board.Speed, self)
            self.msg2Statusbar.emit(str(self.numLinesRemoved))
        # 更新界面
        self.update()

    # 渲染是在paintEvent()方法里发生的QPainter负责PyQt5里所有低级绘画操作。
    def paintEvent(self, event):
        '''paints all shapes of the game'''

        painter = QPainter(self)    # 新建了一个QPainter对象
        rect = self.contentsRect()  # 获取内容区域
        # self.squareHeight()获取的是小方块的高度，不是很理解，猜测是方块出现后去获取方块的高度
        boardTop = rect.bottom() - Board.BoardHeight * self.squareHeight()  # 获取board中除去方块后多出来的空间
        # 渲染游戏分为两步。第一步是先画出所有已经落在最下面的的图，这些保存在self.board里。
        # 可以使用shapeAt()查看这个这个变量。
        for i in range(Board.BoardHeight):
            for j in range(Board.BoardWidth):
                # 返回存储在self.board里面的形状
                shape = self.shapeAt(j, Board.BoardHeight - i - 1)
                # 如果形状不是空，绘制方块
                if shape != Tetrominoe.NoShape:
                    # 绘制方块，rect.left()表示Board的左边距
                    self.drawSquare(painter,
                        rect.left() + j * self.squareWidth(),
                        boardTop + i * self.squareHeight(), shape)
        # 第二步是画出正在下落的方块
        # 获取目前方块的形状，不能为空
        if self.curPiece.shape() != Tetrominoe.NoShape:

            for i in range(4):
                # 计算在Board上的坐标，作为方块坐标原点（单位是小方块）
                x = self.curX + self.curPiece.x(i)
                y = self.curY - self.curPiece.y(i)
                # 绘制方块
                self.drawSquare(painter, rect.left() + x * self.squareWidth(),
                    boardTop + (Board.BoardHeight - y - 1) * self.squareHeight(),
                    self.curPiece.shape())


    def keyPressEvent(self, event):
        '''processes key press events'''

        key = event.key()

        # R代表重启游戏
        if key == Qt.Key_R:
            print("restart game")
            self.initBoard()
            self.start()

        # 如果游戏不是开始状态或者方块形状为空，直接返回
        if not self.isStarted or self.curPiece.shape() == Tetrominoe.NoShape:
            super(Board, self).keyPressEvent(event)
            return

        # P代表暂停
        if key == Qt.Key_P:
            self.pause()
            return
        # 如果游戏处于暂停状态，则不触发按键（只对按键P生效）
        if self.isPaused:
            return
        # 方向键左键代表左移一个位置，x坐标-1
        elif key == Qt.Key_Left:
            self.tryMove(self.curPiece, self.curX - 1, self.curY)
        # 在keyPressEvent()方法获得用户按下的按键。如果按下的是右方向键，就尝试把方块向右移动，说尝试是因为有可能到边界不能移动了。
        # 方向键右键代表右移一个位置，x坐标+1
        elif key == Qt.Key_Right:
            self.tryMove(self.curPiece, self.curX + 1, self.curY)
        # 下方向键代表向右旋转
        elif key == Qt.Key_Down:
            self.tryMove(self.curPiece.rotateRight(), self.curX, self.curY)
        # 上方向键是把方块向左旋转一下
        elif key == Qt.Key_Up:
            self.tryMove(self.curPiece.rotateLeft(), self.curX, self.curY)
        # 空格键会直接把方块放到底部
        elif key == Qt.Key_Space:
            self.dropDown()
        # D键是加速一次下落速度
        elif key == Qt.Key_D:
            self.oneLineDown()

        else:
            super(Board, self).keyPressEvent(event)

    # 在计时器事件里，要么是等一个方块下落完之后创建一个新的方块，要么是让一个方块直接落到底
    def timerEvent(self, event):
        '''handles timer event'''

        if event.timerId() == self.timer.timerId():
            # 如果在消除方块，说明方块已经下落到底部了，创建新的方块，否则下落一行
            if self.isWaitingAfterLine:
                self.isWaitingAfterLine = False
                self.newPiece()
            else:
                self.oneLineDown()

        else:
            super(Board, self).timerEvent(event)

    # clearBoard()方法通过Tetrominoe.NoShape清空broad
    def clearBoard(self):
        '''clears shapes from the board'''
        # 将界面每个小方块都设置为空，存储到self.board中，下标表示第几个方块，（x*y)
        for i in range(Board.BoardHeight * Board.BoardWidth):
            self.board.append(Tetrominoe.NoShape)


    def dropDown(self):
        '''drops down a shape'''
        # 获取当前行
        newY = self.curY
        # 当方块还没落到最底部时，尝试向下移动一行，同时当前行-1
        while newY > 0:

            if not self.tryMove(self.curPiece, self.curX, newY - 1):
                break

            newY -= 1
        # 移到底部时，检查是否能够消除方块
        self.pieceDropped()


    def oneLineDown(self):
        '''goes one line down with a shape'''
        # 调用self.tryMove()函数时，就已经表示方块下落一行了，每次下落到底部后，检查一下是否有能够消除的方块
        if not self.tryMove(self.curPiece, self.curX, self.curY - 1):
            self.pieceDropped()


    def pieceDropped(self):
        '''after dropping shape, remove full lines and create new shape'''
        # 将方块的形状添加到self.board中，非0代表该处有方块
        for i in range(4):
            # 获取每个小方块的坐标
            x = self.curX + self.curPiece.x(i)
            y = self.curY - self.curPiece.y(i)
            self.setShapeAt(x, y, self.curPiece.shape())
        # 移除满行的方块
        self.removeFullLines()
        # self.isWaitingAfterLine表示是否在等待消除行，如果不在等待就新建一个方块
        if not self.isWaitingAfterLine:
            self.newPiece()

    # 如果方块碰到了底部，就调用removeFullLines()方法，找到所有能消除的行消除它们。
    # 消除的具体动作就是把符合条件的行消除掉之后，再把它上面的行下降一行。
    # 注意移除满行的动作是倒着来的，因为我们是按照重力来表现游戏的，如果不这样就有可能出现有些方块浮在空中的现象
    def removeFullLines(self):
        '''removes all full lines from the board'''

        numFullLines = 0    # 记录消除的行数
        rowsToRemove = []   # 要消除的行列表

        for i in range(Board.BoardHeight):  # 遍历每一行

            n = 0
            for j in range(Board.BoardWidth): # 遍历整行的方块
                # 如果self.board里面的值不为空，计数
                if not self.shapeAt(j, i) == Tetrominoe.NoShape:
                    n = n + 1
            # 如果整行都有方块，将要消除的行添加进数组中
            if n == Board.BoardWidth:   # 原文是 n == 10,但我觉得该成n == Board.BoardWidth会更严谨一点
                rowsToRemove.append(i)
        # 因为是从上往下遍历，所以要倒过来消除，否则会出现方块悬空的情况
        # 当然，也可以在遍历的时候这样遍历：for m in rowsToRemove[-1:0]
        rowsToRemove.reverse()

        for m in rowsToRemove:
            # self.shapeAt(l, k + 1)获取要消除的行的上一行的方块形状，然后替换当前方块的形状
            for k in range(m, Board.BoardHeight):
                for l in range(Board.BoardWidth):
                        self.setShapeAt(l, k, self.shapeAt(l, k + 1))

        # 更新已经消除的行数
        # numFullLines = numFullLines + len(rowsToRemove)
        # 还可以改成这样，如果连续消除，则分数翻倍。
        numFullLines = numFullLines + int(math.pow(2, len(rowsToRemove))) - 1

        if numFullLines > 0:
            # 更新分数
            self.numLinesRemoved = self.numLinesRemoved + numFullLines
            self.msg2Statusbar.emit(str(self.numLinesRemoved))  # 改变状态栏分数的值
            # 在消除后还要将当前方块形状设置为空，然后刷新界面
            self.isWaitingAfterLine = True
            self.curPiece.setShape(Tetrominoe.NoShape)
            self.update()

    # newPiece()方法是用来创建形状随机的方块。如果随机的方块不能正确的出现在预设的位置，游戏结束。
    def newPiece(self):
        '''creates a new shape'''

        self.curPiece = Shape() # 创建了一个Shape对象
        self.curPiece.setRandomShape()  # 设置了一个随机的形状
        self.curX = Board.BoardWidth // 2 + 1   # 以界面中心为起点
        self.curY = Board.BoardHeight - 1 + self.curPiece.minY() # 从这里看应该是预留了一行的高度，但不知道作用是什么
        # 判断是否还有空位，如果没有
        if not self.tryMove(self.curPiece, self.curX, self.curY):
            # 将当前形状设置为空
            self.curPiece.setShape(Tetrominoe.NoShape)
            self.timer.stop()   # 停止计时
            self.isStarted = False  # 将开始状态设置为False
            self.msg2Statusbar.emit(f"Game over, your socre is {self.numLinesRemoved}") # 状态栏显示游戏结束
            print(f"Game over, your socre is {self.numLinesRemoved}")


    # tryMove()是尝试移动方块的方法。
    # 如果方块已经到达board的边缘或者遇到了其他方块，就返回False。否则就把方块下落到想要的位置
    def tryMove(self, newPiece, newX, newY):
        '''tries to move a shape'''

        for i in range(4):
            # newPiece是一个Shape对象，newX,newY相当于坐标原点（相对于方块而言）
            x = newX + newPiece.x(i)    # 得到每个小方块在界面上的坐标
            y = newY - newPiece.y(i)
            # 超出边界则返回False
            if x < 0 or x >= Board.BoardWidth or y < 0 or y >= Board.BoardHeight:
                return False
            # 如果方块位置不为0，说明已经用过了，不允许使用，返回False
            if self.shapeAt(x, y) != Tetrominoe.NoShape:
                return False

        self.curPiece = newPiece    # 更新当前的方块形状
        self.curX = newX    # 更新当前的坐标
        self.curY = newY
        self.update()   # 更新窗口，同时调用paintEvent()函数

        return True


    def drawSquare(self, painter, x, y, shape):
        '''draws a square of a shape'''

        colorTable = [0x000000, 0xCC6666, 0x66CC66, 0x6666CC,
                      0xCCCC66, 0xCC66CC, 0x66CCCC, 0xDAAA00]
        # 为每种形状的方块设置不同的颜色
        color = QColor(colorTable[shape])
        # 参数分别为x,y,w,h,color，填充了颜色
        painter.fillRect(x + 1, y + 1, self.squareWidth() - 2,
            self.squareHeight() - 2, color)

        painter.setPen(color.lighter())
        # 画线，从起始坐标到终点坐标，-1是为了留一点空格，看起来更有立体感
        painter.drawLine(x, y + self.squareHeight() - 1, x, y) # 左边那条线
        painter.drawLine(x, y, x + self.squareWidth() - 1, y)   # 上边那条线
        # 换了画笔的样式，同样是为了让图案看起来更有立体感
        painter.setPen(color.darker())
        painter.drawLine(x + 1, y + self.squareHeight() - 1,
            x + self.squareWidth() - 1, y + self.squareHeight() - 1)    # 下边那条线
        painter.drawLine(x + self.squareWidth() - 1,
            y + self.squareHeight() - 1, x + self.squareWidth() - 1, y + 1) # 右边那条线

# Tetrominoe类保存了所有方块的形状。我们还定义了一个NoShape的空形状。
class Tetrominoe(object):
    # 和Shape类里的coordsTable数组一一对应
    NoShape = 0
    ZShape = 1
    SShape = 2
    LineShape = 3
    TShape = 4
    SquareShape = 5
    LShape = 6
    MirroredLShape = 7

# Shape类保存类方块内部的信息。
class Shape(object):
    # coordsTable元组保存了所有的方块形状的组成。是一个构成方块的坐标模版。
    coordsTable = (
        ((0, 0),     (0, 0),     (0, 0),     (0, 0)),   # 空方块
        ((0, -1),    (0, 0),     (-1, 0),    (-1, 1)),
        ((0, -1),    (0, 0),     (1, 0),     (1, 1)),
        ((0, -1),    (0, 0),     (0, 1),     (0, 2)),
        ((-1, 0),    (0, 0),     (1, 0),     (0, 1)),
        ((0, 0),     (1, 0),     (0, 1),     (1, 1)),
        ((-1, -1),   (0, -1),    (0, 0),     (0, 1)),
        ((1, -1),    (0, -1),    (0, 0),     (0, 1))
    )

    def __init__(self):
        # 下面创建了一个新的空坐标数组，这个数组将用来保存方块的坐标。
        self.coords = [[0,0] for i in range(4)]     # 4x4的二维数组，每个元素代表方块的左上角坐标
        self.pieceShape = Tetrominoe.NoShape    # 方块形状，初始形状为空白

        self.setShape(Tetrominoe.NoShape)

    # 返回当前方块形状
    def shape(self):
        '''returns shape'''

        return self.pieceShape

    # 设置方块形状
    def setShape(self, shape):  # 初始shape为0
        '''sets a shape'''

        table = Shape.coordsTable[shape]    # 从形状列表里取出其中一个方块的形状，为一个4x2的数组

        for i in range(4):
            for j in range(2):
                self.coords[i][j] = table[i][j] # 赋给要使用的方块元素

        self.pieceShape = shape # 再次获取形状（index）

    # 设置一个随机的方块形状
    def setRandomShape(self):
        '''chooses a random shape'''

        self.setShape(random.randint(1, 7))

    # 小方块的x坐标，index代表第几个方块
    def x(self, index):
        '''returns x coordinate'''

        return self.coords[index][0]

    # 小方块的y坐标
    def y(self, index):
        '''returns y coordinate'''

        return self.coords[index][1]

    # 设置小方块的x坐标
    def setX(self, index, x):
        '''sets x coordinate'''

        self.coords[index][0] = x

    # 设置小方块的y坐标
    def setY(self, index, y):
        '''sets y coordinate'''

        self.coords[index][1] = y

    # 找出方块形状中位于最左边的方块的x坐标
    def minX(self):
        '''returns min x value'''

        m = self.coords[0][0]
        for i in range(4):
            m = min(m, self.coords[i][0])

        return m

    # 找出方块形状中位于最右边的方块的x坐标
    def maxX(self):
        '''returns max x value'''

        m = self.coords[0][0]
        for i in range(4):
            m = max(m, self.coords[i][0])

        return m

    # 找出方块形状中位于最左边的方块的y坐标
    def minY(self):
        '''returns min y value'''

        m = self.coords[0][1]
        for i in range(4):
            m = min(m, self.coords[i][1])

        return m

    # 找出方块形状中位于最右边的方块的y坐标
    def maxY(self):
        '''returns max y value'''

        m = self.coords[0][1]
        for i in range(4):
            m = max(m, self.coords[i][1])

        return m

    # rotateLeft()方法向右旋转一个方块。正方形的方块就没必要旋转，就直接返回了。
    # 其他的是返回一个新的，能表示这个形状旋转了的坐标。
    def rotateLeft(self):
        '''rotates shape to the left'''
        # 正方形没有必要旋转
        if self.pieceShape == Tetrominoe.SquareShape:
            return self
        # 获取当前的方块形状
        result = Shape()
        result.pieceShape = self.pieceShape
        # 向左旋转，相当将坐标轴向左旋转了，和原来的坐标轴想比 (x,y) -> (y,-x)
        for i in range(4):  # i代表第几个小方块
            result.setX(i, self.y(i))   # 设置第i个方块的x坐标，
            result.setY(i, -self.x(i))  # 设置第i个方块的x坐标

        return result

    # 向右旋转，同理，(x,y) -> (-y,x)
    def rotateRight(self):
        '''rotates shape to the right'''

        if self.pieceShape == Tetrominoe.SquareShape:
            return self

        result = Shape()
        result.pieceShape = self.pieceShape

        for i in range(4):
            result.setX(i, -self.y(i))
            result.setY(i, self.x(i))

        return result


if __name__ == '__main__':

    app = QApplication([])
    tetris = Tetris()
    sys.exit(app.exec_())