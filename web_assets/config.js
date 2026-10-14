/*!
 * Author: Jerman.Xie | xieguishi@126.com
 * Date: 2013.09
 *
 * 数据文件: 
 * 储存初始化的配件数据
 * 储存缓存数据或实际数据
 * 储存任何需要在web中应用到的数据
 */
var Configs = {
	//登录页
	login : "login.html",
    //是否为首页
    HomePage: true,
	isHomePage: function(t){
		return /HomePage/g.test(t)	
	},
    //轮询时,mainBody滚动条所在的位置
    MainScrollHeight: 0,
    //模块
    Modules: {
        Defaults: ["header", "sider", "mainBar", "mainContent"],
        //初始化modules模块,模块的ID名称
        Renders: ["header", "sider", "mainBar", "mainContent", "alarm"] //渲染模块
    },
    //导航
    Navigation: {
        //当前菜单CSS
        current: "currentMenu",
        //导航间隔符
        space: "<span></span>",
        nav: [],
        currentObj: null,
        prevObj: null,
        parentObj: null,
        index: 0
    },
    //模板
    Template: {
        info: {
			//默认数据地址
			data:"/var/datas/data.index.html",
			//默认模板地址
			template:"tmp.index.html"
		},
        //首页模板前缀
	prefix: "tmp_",
        content: {}, //请求的模板,模板可以缓存
		common: []
    },
    //数据
    Data: {
        //请求的实际数据,Object[JSON]
        content: {},
        //前次请求的缓存数据,String,不管数据是否完整都存储在此
        cache: "",
        //判断数据完整
        complete: false,
        //允许请求失败的最大次数,interval*getFailMax毫秒
        failMax: 6,
        //当前默认获取失败的次数
        failNum: 0,
        //通讯中断,默认为false,表示通讯正常
        fail: false,
        //判断数据完整的结尾符
        endStr: "\"%__data_end__%\"",
        //数据不完整时，请求的时间间隔,比正常的interval快
        intervalUp: 2000,
        //返回不完整数据时，会加快更新数据的频率，intervalCache用来恢复正常的频率,请设置与interval一样的值
        intervalCache: 5000,
        //间隔请求数据的时间,5s
        interval: 5000,
		//默认轮询时间，用于自定义轮询时间后的恢复
		defaultInterval: 5000,
        //单次请求超时时间
        timeout: 5000,
		//默认超时时间，与timeout相等。用于自定义超时后的恢复
		defaultTimeout: 5000,
        //页面是否需要轮询
        polling: true,
        //setting页面,当前输入的值,其他用户修了页面，渲染页面时会把当前输入值写入输入框
        setting: {},
        //判断是否渲染页面，默认为true，如果为false,页面更新会被阻止
        render: true
    },
    //告警
    Alarm: {
        //告警数据URL
        url: "/var/datas/data.alarms.html",
        //缓存的alarm数据
        cache: "",
        //缓存告警列表个数
        cacheLength: 0,
        //alarm数据
        data: {},
        //alarm请求数据时间
        interval: 5000,
        //alarm是否隐藏,默认为false，即alarm默认为收缩状态
        show: false,
        //alarm在有新更新时，是否自动弹出1->自动弹出,0->不自动弹出
        auto: 1,
        //alarm当前显示tab
        tab: 0,
        //alarm滚动的位置,有新告警生成时，还是保持在这个位置
        scrollHeight: 0,
        //alarm查看状态
        expand: false,
        //允许请求失败的最大次数,interval*getFailMax毫秒
        failMax: 6,
        //当前默认获取失败的次数
        failNum: 0,
        //alarm请求次数
        requestCount:0,
        //alarm强制刷新,默认请求60次(即5分钟)时，强制刷新一次
        refresh: 60,
	timeout: 10000
    },
    //Hybrid曲线
    Hybrid: {
        data: {},
        lines: {},
        week: 1
    },
    //趋势图
    Trend: {
        url: "/var/datas/data.index_trend.html",
        dataCache: "",
        data_y: {},     //未转化百分之前的数据
        data: {},       //转化百比之后的数据
        tempInterval: 2000,
        //如果第一次请求trend失败,则2秒请求一次，直到请求完成
        interval: 3600000,
        //趋势图一小时更新一次数据,前端一小时10秒更新,确保更新时,数据已经更新了
        failNum: 0,
        //加载失败的次数
        failMax: 6,
        //由于数据文件未生成，或网络错误导致加载失败最大的次数
        fail_200: false, //trend数据返回200,如果因为不完整或json格式错误，则设置为true,否则为false
        Enter: false, //鼠标是否进入趋势图区域，如果进入趋势图区域，则可以使用左右箭头控制查看点的值
        Point: 0   //趋势图鼠标经过当前所在点
    },
    //负载趋势图画布宽度
    TrendCvWidth:600,
    ChartdrawCurve_Y:[17,19,28,28],
    //cookies key
    Cookies: {
        names: [],
        path: "/"
    },
    //协议类型,0---EEM，1---YDN23，2---Modbus,Modbus预留
    protocol_type: null,
    //请求的数据文件中，公共的部分
    Commons: {
        solar: null,
        converter: null
    },
    Popup: {
        index: null,
        status: false,
        scrollHeight: 0
    },
    Sider: {
        Controller: []
    },
    //是否屏蔽后退键
    Backspace: false,
    //是否保持与系统连接
    KeepActive: true,
    //显示系统时间的格式
    TimeFormat: 0,
    //所在时区
    timezone: 0,
    //系统时间
    SystemTime: "",
    //浏览器类别
    Browser: "",
    //计数进入首页的次数（轮询除外）,超过10次则reload()一次，以清除使用的DOM，释放内存
    ClickHomeNum: 0,
    ClickHomeMax: 10,
    //系统重启倒计时间
    RestartTime: 200,
    Chart: {},
    //单击菜单间隔时间,默认不能快于350ms
    ClickInterval: 350,
    TabIndex: 0,
    PowerSystem: [],
    //高亮行
    HighLight: null,
    StopReload: false,
    UploadTimeout: null,
    //设置相关页面,保存当前焦点的<select>
    SelectFocus: null,
	//页面中临时设置的setTimeout或setInterval，如果在这个延时过程中通过单击跳转到了别的页面，则会在bindEvent中把它取消;
	tmpTimer:[],
	//哪些页面需要在窗口或alarm告警窗口变动时，重新刷新
	//为true,直接刷新,为数组时，格式为：[true,function],第1位为true时执行function
	//如cabinet set页面,左边branch和右边方格高度是随窗口变化而变化的
	refresh:false,
	//记录body滚动的高度
	bodyScroll:0,
	//是否刷新告警信息
	refreshalarm:true
};