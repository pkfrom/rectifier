/*!
 * Author: Jerman.Xie | xieguishi@126.com
 * Date: 2013.09
 *
 * Views控制器: 
 * 负责页面各种展示效果
 * 负责页面中的各种事件
 */
var Pages = {
    /* 删除数组的某些值*
    * arr: 数组
    * value: 数组->被删除的项
    */
    DelArrayValue: function (arr, value) {
        if ($.type(arr) != "array" || $.type(value) != "array") { return arr; }
        for (var i = 0, ilen = arr.length; i < ilen; i++) {
            for (var j = 0, jlen = value.length; j < jlen; j++) {
                if (arr[i] == value[j]) {
                    arr.splice(i, 1);
                }
            };
        };
        return arr;
    },
    /*---------------------------------*
    * current: 参数=>秒数
    * return : 返回UTC时间
    *---------------------------------*/
    GetUTCtime: function (current) {
        /*current传入为秒数*/
        var starttime = new Date("1970/01/01 00:00:00").getTime() / 1000;
        return new Date((current + starttime) * 1000);
    },
	/*获取入口链接上的'data'数据，并初始化某些数据*/
	GetAttrData: function(target){
		var $this = $(target);
		if(!target){ return ''; }
		var data = jQuery.evalJSON($this.attr('data').replace("{,", "{"));
		if (!data["fn"]) {
			data['fn'] = null;
		}
		if (!data['modules']) {
			data['modules'] = "mainContent";
		}
		if (!data['menuIndex']) {
			data['menuIndex'] = 1;
		}
		data['text'] = data['title'] ? data['title'] : $this.text() || "";
		if(!data['currentMenu']){
			var pNodeName = $this.parent()[0].nodeName;
			switch (pNodeName) {
				case "DIV":
					var pid = $this.parent().attr("id");
					if(pid){
						if (pid == "mainTab") {
							var tIndex = $this.index();
							data['currentMenu'] = ["#mainTab a", tIndex];
						} else if (pid == "mainTabContent") {
							var tIndex = $this.index();
							data['currentMenu'] = ["#mainTabContent a", tIndex];
						} else {
							data['currentMenu'] = ["#" + pid+ " a", 0];
						}
					} else {
						var pclass = $this.parent().attr("class");
						if(pclass){
						   data['currentMenu'] = ["."+$this.parent().attr("class").split(" ")[0]+" a",0];
						} else {
						   data['currentMenu'] = ["#mainContent a",0];
						}
					}
					break;
				case "LI":
					var tIndex = $this.parent().index();
					data['currentMenu'] = ["ul.sider-list a", tIndex];
					break;
				default:
					data['currentMenu'] = [];
			}
		}
		data['sessionId'] = jQuery.cookie("sessionId");
		data['level'] = Number(jQuery.cookie("nAuthority"));
		data['language_type'] = Number(jQuery.cookie("language_type"));
		return data;
	},
	/*初始化某些数据*/
	InitData:function(data){
		Configs.HighLight = null;
		Configs.Modules.Defaults = ["mainBar", "mainContent"];
		//初始化弹出层数据
		Configs.Popup.Data = null;
		//解除页面更新阻止
		Configs.Data.render = true;
		//创建历史记录
		$.history.set(data);
		//恢复mainBody scroll
		$("#mainBody").css("overflow-y","auto");
		//删除power system页面记录
		Configs.PowerSystem = [];
		//取消页面延时
		var timers = Configs.tmpTimer;
		if(timers){
			for(var i=0,ilen=timers.length; i< ilen; i++){
				clearTimeout(timers[i]);
				clearInterval(timers[i]);
			};
		}
		//清除modules上可能存在的利用jQuery.data()缓存的数据
		var cacheData = $("#"+data["modules"]);
		if(cacheData[0]){
		    cacheData.removeData();
		}
	},
    /*---------------------------------*
    * 为模块内绑定事件，并初始化args数据对象传递到最终的模板和回调函数当中
    *---------------------------------*/
    bindEvent: function (evt, eleid, popEle) {
        var that = this;
        var ele = $(eleid);
        //绑定单击事件
        if (ele.length > 0 && popEle) {
            ele.off().on(evt, popEle, function (event) {
                var $this = $(this);
		if($this.parent()[0].id=="mainTabContent"){
			var mainContent = $("#mainContent");
			var tabCache = mainContent.data("tabs");
			if(tabCache && mainContent[0]){
				mainContent.data("tabs").TabsCurrent = $this;
			}
		}
                if (!$this.attr("data")) {
                    return false;
                };
                try {
                    var data = that.GetAttrData($this);
                } catch (err) {
                    alert(Language.Html["030"]);
                    return false;
                }
				that.InitData(data);
                //把data(即后文的args)传递到模板当中
                Control.GetTemplate(data);
                return false;
            });
        };
        ele = null;
    },
    /*---------------------------------*
    * 记录id="mainBody"的滚动高度,以便轮询更新中数据改变时，恢复到当前滚动的位置
    *---------------------------------*/
    setScroll: function () {
		var mainBody = $("#mainBody"),self=this;
		if(mainBody[0]){
			mainBody.off("scroll").on("scroll", function () {
				Configs.MainScrollHeight = $(this).scrollTop();
				clearTimeout(self.scroll_timer);
				self.scroll_timer = setTimeout(function(){
					self.ResetHighLight(true);
				},100);
			})
			
		}
		$(document).off("scroll").on("scroll",function(){
			Configs.bodyScroll = $(this).scrollTop();
		});
    },
	/*
	 * scroll-> 为true,指在mainBody的"scroll"事件中调用
	 * scroll-> 为false,指在CallBack()函数后面调用,只是最后定位mainBody的滚动高度
	 */
	ResetHighLight:function(scroll){
		var doc=document, mainBody = $(doc.getElementById("mainBody")),HighLight = doc.getElementById(Configs.HighLight);
		if(HighLight){
			$(HighLight).addClass("select");
			if(scroll){
				var top = $(HighLight).offset().top;
				if(top < 170 || top-mainBody.height()>140){
					//滚动隐藏后，取水高亮
					$(HighLight).removeClass('select');
					Configs.HighLight = null;
					//删除输入框数据
					var Eles = $(HighLight).find(".set_value");
					var isRadio = Eles.find("input");
					if(isRadio.length>0){
						isRadio.eq(0).prop("checked", true);
					} else {
						Eles.val("").blur();
					}
					Configs.Data.setting = {};
				} else {
					//
				}
			}
		}
		if(!scroll){
			//定位mainBody滚动高度
			mainBody.scrollTop(Configs.MainScrollHeight);
		}
	},
	/*
	 * as->所有链接
	 * parent->所有链接外围<div>
	 * sw->一页显示的宽度，默认为726
	 * tabsData->tabs数据缓存
	*/
	TabsNavIndex: function(as,parent,sw,tabsData){
		var asLen = as.length;
		//分页数,pages为一个数组,存储分页显示哪些导航
		var pages = [];
		var mw = $(parent).innerWidth();
		if(mw<=sw){ return false; }
		//如果所有宽度大于sw(默认为720)，则分页
		var aw = 0;
		for (var i = 0, ilen = as.length; i < ilen; i++) {
			var asi = as.eq(i);
			var asiWidth = asi.outerWidth(true);
			aw += asiWidth;
			if(aw>sw){
				pages.push(i);
				aw = asiWidth;
			}
		};
		//分别储存分页链接
		var alist = [];
		//页数是pages长度+1;
		for(var p=0,plen=pages.length; p<=plen; p++){
			if(p==0){
				alist.push(as.slice(0,pages[p]));
			} else if(p==plen){
				alist.push(as.slice(pages[p-1],asLen));
			} else {
				alist.push(as.slice(pages[p-1],pages[p]));
			} 
		}
		tabsData.TabsPage = alist;
		return true;
	},
	//统一自定义下拉列表
	BindSelect:function(pageobj){
	     $(".input_select").off().click(function (event,pro) {
	     var setTop = $(this).offset().top;
	     //判断是否是trigger触发事件
	     if(pro!="tig"){
               var cutobj=$(this).next(".language");
               var optionheight=cutobj.find("li").length*19;
               cutobj.css({"width":""+Number($(this).width()+7)+"px"});
               if(cutobj.hasClass("yinc")) {
                   //当下拉选项高度大于下拉框距离底部的高度时向上展开(不能向下完整展开)
                   if(optionheight>(document.documentElement.clientHeight - setTop-22-35)){
                        //当下拉选项高度大于下拉框距离顶部的高度时向下展开并添加滚动条
                        if(optionheight>setTop){//向下展开
               		        //如果下面不足以显示三项option就在上面显示（22：下拉列表文本框高度；35底部footer的高度；19下拉列表选择框高度；10：下拉列表距离底部footer的高度）
           		            if(document.documentElement.clientHeight - setTop-22-35>19*3){
           		        	    cutobj.css({"margin-top":"0px","height":document.documentElement.clientHeight - setTop-22-35-10,"overflow":"auto"});
						    }else{//向上展开并添加滚动条
							    cutobj.css({"margin-top":"-"+(optionheight+21-(optionheight-(setTop-166-10)))+"px","height":""+setTop-166-10+"px","border-bottom":"0px","border-top":"1px","overflow": "auto"});
							}
               	        }else{//向上展开
               	            //如果下拉框高度超过body的范围则修改浮动方式为固定fixed
                            if(optionheight>setTop-166){
           	                    cutobj.css({"margin-top":"-"+(optionheight+21-(optionheight-(setTop-166-10)))+"px","height":""+setTop-166-10+"px","border-bottom":"0px","border-top":"1px","overflow": "auto"});
           	                }else{
                                cutobj.css({"margin-top":"-"+(optionheight+21)+"px","height":"auto","border-top":"1px #8F8F8F solid"});
                            }
               	        }
                   }else{
               		    cutobj.css({"margin-top":"0px","height":"auto"});
                   }
                   cutobj.slideDown(50).removeClass("yinc");
                   cutobj.find("li").slideDown(50).removeClass("yinc");
               }else{
                   cutobj.slideUp(10).addClass("yinc");
                   cutobj.find("li").slideUp(10).addClass("yinc");
               }
            }
         });
         $(document).off("click").click(function (event) {
               if($(event.target).prop("className")!="input_select set_value"&&$(event.target).prop("className")!="language"&&$(event.target).prop("className")!="input_select set_value set_newval") {
                   $(".language").slideUp(20).addClass("yinc");
                   $(".language").find("li").slideUp(20).addClass("yinc");
                   //下拉列表隐藏时开启页面刷新条件
                   Configs.SelectFocus = null;
                   Configs.Data.render = true;
               }
                $(".input_select").next(".language").not($(event.target).next(".language")).slideUp(20).addClass("yinc");
                $(".input_select").next(".language").not($(event.target).next(".language")).find("li").slideUp(20).addClass("yinc");
         });
         $(".language li").click(function (event) {
               $(this).parent().prev(".input_select").text($(this).text()).attr("data-index",$(this).find("a").attr("rel"));
               $(this).parents(".language").slideUp(10).addClass("yinc");
               $(this).parents(".language").find("li").slideUp(10).addClass("yinc");
               var oElem = event.target ? event.target : event.srcElement;
               if($(oElem).parents(".dropdown").find("div").prop("id")=="AID_Equip"){//TL1 AID Signal
                   if(pageobj!=""&&pageobj!=undefined&&pageobj!=null){
                      pageobj(event);
                   }
               }else if($(oElem).parents(".dropdown").find("div").prop("id")=="AID_Group"){//TL1 AID Signal
				   return false;
               }else{//Power Split
                   if(pageobj!=""&&pageobj!=undefined&&pageobj!=null){
                     pageobj($(this).parent().prev());
                   }
               }
         });
	},
	//统一自定义单选按钮
	BindRadio:function(){
	    $(".radiodiv").click(function(){
	         if($(this).hasClass("radiodivnot")){
	            $(this).parent(".set_value").children().not(".radiodivnot").addClass("radiodivnot");
	            $(this).removeClass("radiodivnot");
	        }
	    });
	},
	//统一自定义复选框
	BindCheckBox:function(){
	     $(".divcheckbox").click(function(){
	         if($(this).hasClass("divchecked")){
	            $(this).removeClass("divchecked");
	         }else{
	            $(this).addClass("divchecked");
	         }
	    });
	},
	TabsNavSlice: function(data){
		//判断mainTabContent是否存在,要分布必须满足mainTabContent层存在 
		var mainTabContent = $("#mainTabContent");
		if(!mainTabContent[0]){ return false; }
		//设置默认分页宽度sw
		var sw = 1110,that = this;
		//缓存数据存储在mainContent上面
		var mainContent = $("#mainContent"),mainTab = $("#mainTab");
		mainContent.data("tabs",{
			TabsPage: [],
			TabsPageCurrent: 0,
			TabsCurrent: null
		});
		var tabsData = mainContent.data("tabs");
		//获取所有链接、当前链接
		var as = mainTabContent.find("a"),ac = mainTabContent.find("a.currentMenu");
		tabsData.TabsCurrent = ac;
		//为导航分页
		var hasPage = this.TabsNavIndex(as,mainTabContent,sw,tabsData);
		//获取左右按钮
		var btnLeft = mainTab.find("a.tab-al"),btnRight = mainTab.find("a.tab-ar");
		var ClassRD = "tab-ar-disabled",ClassLD="tab-al-disabled";
		//初始化右按钮
		if(hasPage){
			btnRight.removeClass(ClassRD);
		} else {
		    btnRight.addClass(ClassRD);
			return;
		}
		//默认分割
		mainTabContent.html(tabsData.TabsPage[0]);
		var checkmenu = function(){
			mainTabContent.html(tabsData.TabsPage[tabsData.TabsPageCurrent]);
			var acc = mainTabContent.find("a.currentMenu")
			if(!acc.is(tabsData.TabsCurrent)){
				acc.removeClass("currentMenu");	
			}
			that.bindEvent("click", mainTabContent, "a");
		}		
		//绑定右单击事件
		btnRight.off("click").on('click',function(){
			if($(this).hasClass(ClassRD)){ return false; }
			tabsData.TabsPageCurrent++;
			checkmenu();
			btnLeft.removeClass(ClassLD);
			if(tabsData.TabsPageCurrent==tabsData.TabsPage.length-1){
				$(this).addClass(ClassRD);	
			}
		});
		//绑定左单击事件
		btnLeft.off("click").on('click',function(){
			if($(this).hasClass(ClassLD)){ return false; }
			tabsData.TabsPageCurrent--;
			checkmenu();
			btnRight.removeClass(ClassRD);
			if(tabsData.TabsPageCurrent==0){
				$(this).addClass(ClassLD);	
			}
		});
	},
	/*
	    在span中单选按钮放置不下则换行显示
	*/
    ReviseRadio:function(){
        var fieldsetobj=$("fieldset");
        for(var i=0;i<fieldsetobj.length;i++){
           var outwidth=$("fieldset").eq(i).width();
           var radiowidth=0;
           $.each($("fieldset").eq(i).children(),function(){
                radiowidth+=$(this).outerWidth(true);
           })
           if(radiowidth>=outwidth){
                $("fieldset").eq(i).find("div").css({"margin-top":"5px"});
           }
        }
	},
	/*对input绑定相关事件*/
	bindInput: function () {
        $("input").off("focus blur keydown").on("focus", function () {
            //如果redonly为true，一般为时间设置，即不可以使用backspace
            if (!$(this).attr("readonly")) {
                Configs.Backspace = true;
            }
        }).on("blur", function () {
            Configs.Backspace = false;
        }).on("keydown", function () {
            if ($(this).hasClass("set_value")) {
                Configs.Backspace = true;
            };
        });
    },
    /*---------------------------------*
    * 模块运行调用的回调函数,在链接中,设置 data = {"fn":calback}
    *---------------------------------*/
    CallBack: function (data) {
		//循环运行fn中的回调函数
        var fn = data.args['fn'] || [];
        for (var i = 0, ilen = fn.length; i < ilen; i++) {
            if (fn[i] && $.type(this[fn[i]]) === "function") {
                this[fn[i]](data);
            };
        };
        //是否禁用backspace退格键
        this.bindInput();
		//重置高亮和滚动位置
		this.ResetHighLight();
    },
    /*---------------------------------*
    * mainContent为主窗口，所有模块都会在mainContent加载，所以都会首先运行mainContent方法
    * 如果链接data={}属性中，modules为空或modules="mainContent" 就会运行mainContent方法
    *---------------------------------*/
    mainContent: function (data) {
		//移除页面loading
        var ModuleLoading = document.getElementById("ModuleLoading");
        if (ModuleLoading && $(ModuleLoading).is(":visible")) {
            ModuleLoading.style.display = "none";
			ModuleLoading = null;
        }
        //为tab中的链接绑定单击事件
        this.bindEvent("click", "#mainTab", "a");
		//设置当前滚动位置
        this.setScroll();
		//设置tab导航栏分页
        this.TabsNavSlice(data);
    },
    /*---------------------------------*
    * 进行了mainContent加载后，tab导航的内容会在mainBody里加载，所以单击tab，首先会运行mainBody
    * 如果链接data={}属性中，modules="mainBody" 就会运行mainBody方法
    *---------------------------------*/
    mainBody: function (data) {
		//设置当前滚动位置
        this.setScroll();
	},
    /*---------------------------------*
    * footer模块的回调函数
    *---------------------------------*/
    footer: function (data) {
	var isData =  data && data.data;
	var dataFormat = isData && data.data.time_format;
	var isTime = isData && data.data.present_time;
        if (dataFormat) {
            Configs.TimeFormat = data.data.time_format;
        }
        var that = this;
        //设置显示系统时间
		var timezone = new Date().getTimezoneOffset() / 60;
        var system_time = $("#SystemTime").find("span")[0];
		if(isTime){
			var current = data.data.present_time;
		} else if(Configs.SystemTime!="") {
			current = new Date(Configs.SystemTime-timezone * 3600).getTime()/1000;
		}
        if (!current) { return; }
        function set_current_time() {
            var time = new Date(1000 * (current + timezone * 3600));
            var year = time.getFullYear();
            var month = Validates.MakeupZero(time.getMonth() + 1);
            var day = Validates.MakeupZero(time.getDate());
            var hour = Validates.MakeupZero(time.getHours());
            var minute = Validates.MakeupZero(time.getMinutes());
            var second = Validates.MakeupZero(time.getSeconds());
            var timeStr = "";
            var HMS = hour + ":" + minute + ":" + second;
            switch (Number(Configs.TimeFormat)) {
                case 0:
                    timeStr += day + "-" + month + "-" + year;
                    break;
                case 1:
                    timeStr += month + "-" + day + "-" + year;
                    break;
                case 2:
                    timeStr += year + "-" + month + "-" + day;
                    break;
            };
            timeStr += " " + HMS;
            Configs.SystemTime = year + "/" + month + "/" + day + " " + HMS;
            if (system_time) {
                system_time.innerHTML = timeStr;
            };
        }
        set_current_time();
    },
    /*---------------------------------*
    * header模块的回调函数
    *---------------------------------*/
    header: function (data) {
        //为退出按钮绑定退出事件
        var logout = $("#headerLogout");
        logout.off("click").on("click", function () {
            if (confirm(Language.Html['012'])) {
                Control.LoginOut();
            }
            return false;
        });
        //设置protocol_type，用于维护页面的协议选择
        Configs.protocol_type = data.data.protocol_type ? data.data.protocol_type : 0;
        this.SetCommons();
    },
    /*---------------------------------*
    * sider模块的回调函数(左侧导航)
    *---------------------------------*/
    sider: function (data) {
        var siderList = $("#sider ul.sider-list");
        this.SetCommons();
        //绑定单击事件
        this.bindEvent("click", siderList, "a");
        var SiderInfoList = $("div.sider-info").find("dl");
        SiderInfoList.find("dd:odd").css({ "background": "#D4E0EF" }).end().find("dd:even").css({ "background": "#EAF0F7" });
        //转向ACU+;
        var LinkToACU = document.getElementById("LinkToACU");
        if (LinkToACU) {
            var that = this;
            $(LinkToACU).off().on("click", function () {
                if (!(/IE/g.test(Configs.Browser))) {
                    alert(Language.Html['048']);
                    return false;
                }
                that.SetProcess(Language.Html['049']);
                var XHR = $.ajax({
                    timeout: Configs.Data.timeout,
                    url: "/cgi-bin/web_cgi_main.cgi?user_name=" + jQuery.cookie("user_name") + "&user_password=" + jQuery.cookie("user_password") + "&language_type=" + jQuery.cookie("language_type") + "&_" + new Date().getTime(),
                    success: function (data, textStatus, jqXHR) {
                        jQuery.cookie("acuIP", window.location.hostname, { path: "/" });
                        that.SetProcessRemove();
                        var LinkOldPage = window.open('/cgi-bin/eng/p01_main_frame.htm');
                        LinkOldPage.opener = null;
                        LinkOldPage = null;
                    },
                    error: function (data, textStatus) {
                        that.SetProcessRemove();
                        alert(Language.Html['050']);
                    }
                }).always(function (jqXHR, textStatus, errorThrown) {
                    jqXHR = null;
                    textStatus = null;
                    errorThrown = null;
                    XHR = null;
                });
                return false;
            });
        }
    },
    SetCommons: function (data) {
        var SideSite = $("#SideSite"),
            SideVoltage = $("#SideVoltage"),
            SideCurrent = $("#SideCurrent"),
	    SideConverterVoltage = $("#SideConverterVoltage"),
            SideConverterCurrent = $("#SideConverterCurrent");
        var data = Configs.Alarm.data;
        var lang = jQuery.cookie("language_type");
        //设置site name
        if (SideSite[0] && data.site) {
            SideSite.html(data.site[2][lang]);
        };
        //设置电压电流
        if (SideCurrent[0] && SideVoltage[0] && data.status) {
            SideVoltage.html(Validates.CheckValueReturn(data.status[0], "V"));
            SideCurrent.addClass(Validates.CheckValue(data.status[1], true));
            SideCurrent.html(Validates.CheckValueReturn(data.status[1], "A"));
        }
	//设置Converter电压电流
        if (SideConverterVoltage[0] && SideConverterCurrent[0] && data.converter) {
            SideConverterVoltage.html(Validates.CheckValueReturn(data.converter[0], "V"));
            SideConverterCurrent.addClass(Validates.CheckValue(data.converter[1], true));
            SideConverterCurrent.html(Validates.CheckValueReturn(data.converter[1], "A"));
        }

    },
    /*---------------------------------*
    * alarm(活动告警)模块的回调函数
    *---------------------------------*/
    alarm: function (data) {
        var that = this;
        //预载alarm的各dom节点
        var alarm = $("#alarm");
        var mainContent = $("#mainContent");
        var content = $("#content");
        var autoAlarm = $("#autoAlarm");
        var alarm_list = $("#alarmList div.tab_item");
        var alarmTab = alarm.find("ul.alarm-tab");
        var alarmTip = $("#alarmTip");
        var alarmHandle = alarm.find("a.alarmHandle");
        var alarmtype=[];
        for(var i=0;i<data.Content.length;i++){
            if((data.Content[i][0]==1&&$.inArray(1, alarmtype))||(data.Content[i][0]==2&&$.inArray(2, alarmtype))||(data.Content[i][0]==3&&$.inArray(3, alarmtype))){
                alarmtype.push(data.Content[i][0]);
            }
        }
        
        //设置首页alarm图标状态
         if($.inArray(3, alarmtype)>-1){
            alarmTip.attr("class","h-s-alarm3");
        }else if($.inArray(2, alarmtype)>-1){
            alarmTip.attr("class","h-s-alarm");
        }else if($.inArray(1, alarmtype)>-1){
            alarmTip.attr("class","h-s-alarm1");
        }else{
            alarmTip.attr("class","h-s-ok");
        }
        //alarmTip.attr("class", data.Content.length == 0 ? "h-s-ok" : "h-s-alarm");
        //绑定隐藏显示操作
        var H_alarmMax = 198;
        var H_alarmMin = 28;
        alarmHandle.off().on("click", function (event, index) {
            Configs.startTime = Number(new Date().getTime());
            Configs.Alarm.show = Configs.Alarm.expand ? false : !Configs.Alarm.show;
            Configs.Alarm.expand = false;
            Control.SetLayout();
			Control.RefreshModule(Configs.refresh);
            return false;
        });
        alarmTab.find("li.alarmPop").off().on("click", function () {
            if (!Configs.Alarm.show) {
                Configs.Alarm.show = true;
                Control.SetLayout();
            }else{
            	if(Configs.Alarm.tab == $(this).index()){
            		 alarmHandle.trigger("click");
            	}
            }
            Configs.Alarm.tab = $(this).index();
        });
        //告警类型切换事件
        $(alarm).off().Tabs({
            event: 'click',
            currentTab: Configs.Alarm.tab,
            handle: alarm.find('div.alarm-bar'),
            content: alarm.find('div.alarm-content')
        });
        //告警是否自动弹出,alarmAutoPop写入cookie中保存
        var alarmAutoPop = jQuery.cookie("alarmAutoPop");
        //绑定是否自动弹出事件
        $(autoAlarm).prop("checked", Boolean(Number(alarmAutoPop)));
        $(autoAlarm).off().on("click", function () {
            jQuery.cookie("alarmAutoPop", Number($(this).prop("checked")), { path: "/" });
        });
        if (!Configs.Alarm.show) {
            var DatasPolling = true;
            //如果数据有轮询，则轮询时才弹出alarm,如果没有轮询，则一定弹出alarm
            if (Configs.Data.polling) {
                DatasPolling = Control.isPolling;
            }
            if (Number(alarmAutoPop) == 1 && DatasPolling) {
                if (data.Content.length > Configs.Alarm.cacheLength) {
                    alarmHandle.trigger("click");
                    Configs.Alarm.show = true;
                } else {
                    alarmHandle.addClass("alarmOpen");
                }
            }
        }
        Configs.Alarm.cacheLength = data.Content.length;
        //轮询时,如果有滚动浏览,则记录当前滚动位置,有新增告警或减少的警告,浏览的位置不变.确保用户浏览不受后台轮询更新的影响
        var alarmList = $("#alarmList");
        var alarmpopup = alarmList.find("div.alarm-popup");
        alarmList.off().on("scroll", function () {
            Configs.Alarm.scrollHeight = $(this).scrollTop();
            //滚动时，如果有弹出层信息，则隐藏它
            alarmpopup.hide();
        });
        alarmList.scrollTop(Configs.Alarm.scrollHeight);
        if (Configs.Alarm.expand) {
            Control.SetLayout(true);
        }
        //绑定告警提示,单击后弹出提示
        alarmList.find("ul li.alarm-tip").off().on("click", "i", function () {
            that.PopupInfo("#alarmList", "click", "i", ["div.alarm-popup"], { info: $(this).attr("info"), alarm: true, hide: true });
        });
        //操作sider,因为Controller数据要实时显示,而alarm是全局实时轮询的
        Configs.Sider.Controller = data.controller;
        SetSiderController();
        var do_sider = setInterval(function () {
            SetSiderController();
        }, 300);
        function SetSiderController() {
            var controllers = $("dd.SiderController");
            if (controllers.length == 0) { return; }
            var hidden = 0;
            for (var i = 0, ilen = controllers.length; i < ilen; i++) {
                if (data.controller[i] != 0 && controllers.eq(i)[0]) {
                    controllers.eq(i).find("em").html(data.controller[i]).end().show();
                    controllers.eq(i).css({ "background": i % 2 == (hidden % 2 == 0 ? 1 : 0) ? "#EAF0F7" : "#D4E0EF" });
                } else {
                    controllers.eq(i).hide();
                    hidden++;
                }
            };
             //移动系统状态和配置信息
            $("#siderinfo").children("dd,dl").remove();$("#siderinfo").append($("#sider div").eq(0).html()).addClass("sider-info");
			Control.SetLayout();
            clearInterval(do_sider);
            do_sider = null;
        };
    },
    /*---------------------------------*
    * 导航条模块预留回调函数(当前为空函数)
    *---------------------------------*/
    mainBar: function () {
        var nav = $("div.mainBar-nav");
        //绑定单击事件
        this.bindEvent("click", nav, "a");
    },
    /*---------------------------------*
    * 首页趋势图回调函数
    *---------------------------------*/
    HomeTrend: function (target) {
        //data为函数成百分比后的数据
        var data = Configs.Trend.data;
        //data_y为未转化成百分比前的原始数据
        var data_y = Configs.Trend.data_y;
        data.canvas = {};
        data.canvas.width = Configs.TrendCvWidth;
        data.canvas.height = 110;
        data['fn_nodata'] = function () {
            var AverageCurrent = $("#AverageCurrent")[0];
            if (AverageCurrent) {
                AverageCurrent.innerHTML = "---";
            }
        };
        data['fn'] = function () {
            var AverageCurrent = $("#AverageCurrent");
            var v_checkclass = Validates.CheckValue(data.averageCurrent);
            AverageCurrent.parent("p").attr("class", v_checkclass);
            if (AverageCurrent[0]) {
                AverageCurrent[0].innerHTML = data.averageCurrent + "A";
            }
        };
        Chart.drawCurve("Trend", data, data_y);
        //Trend峰值处理
        if (data.peakCurrent) {
            var PeakCurrent = document.getElementById("PeakCurrent");
            var PeakCurrentTime = document.getElementById("PeakCurrentTime");
            if (PeakCurrent) {
                PeakCurrent.innerHTML = data.peakCurrent[0];
            }
            if (PeakCurrentTime) {
                PeakCurrentTime.innerHTML = data.peakCurrent[1];
            };
        }
    },
    GetCurveData: function (args) {
        var that = this;
        var url = (args && args["url"]) ? args["url"] : "/var/datas/data.hybrid.html";
        var name = (args && args["name"]) ? args["name"] : null;
        var XHR = $.ajax({
            timeout: Configs.Data.timeout,
            url: url + "?_" + new Date().getTime(),
            beforeSend: function () {
                Control.PromptEvent.Loading({ target: "PromptPop", marginTop: "center", clear: false });
            },
            success: function (data, textStatus, jqXHR) {
                var re = new RegExp(Configs.Data.endStr, 'g');
                if (re.test(data)) {
                    Configs.Data.complete = true;
                    data = data.replace(Configs.Data.endStr, "");
                } else {
                    //数据不完整
                    Control.PromptEvent.Tip({ target: "PromptPop", text: Language.Html['005'], marginTop: "center" });
                    return;
                };
                try {
                    data = jQuery.evalJSON(data);
                    if (name != null) {
                        data = data[name];
                    }
                    data = $.extend(true, data, args["setting"]);
                    setTimeout(function () {
                        Chart.drawCurve("Pop" + name + "Curve", data);
                        Control.PromptEvent.LoadingRemove({ remove: "PromptPop" });
                    }, 100);
                } catch (Error) {
                    Control.PromptEvent.Tip({ target: "PromptPop", text: Language.Html['001'], marginTop: "center" });
                    return;
                }
            },
            error: function (data, textStatus) {
                Control.PromptEvent.Tip({ target: "PromptPop", text: Language.Html['021'], marginTop: "center" });
            }
        }).always(function (jqXHR, textStatus, errorThrown) {
            jqXHR = null;
            textStatus = null;
            errorThrown = null;
            XHR = null;
        });
    },
    /*---------------------------------*
    * 弹出层，主要用在了rectifier、converter、solar、battery、alarm模块或页面中
    * 参数： target->绑定对象,evt->绑定事件,ele->冒泡元素,id->模板(同时也是弹出层),data->数据
    *---------------------------------*/
    PopTimer: null,
    PopupInfo: function (target, evt, ele, id, data) {
        var popup = id==null ? null : $(id[0]);
	var mainBody = $("#mainBody");
	var template = "";
	if(popup && popup[0]){
		template = doT.templateChild(popup.attr("template"));
	}
        if (data.close === true) {
            template += "<a class='popup-close' id='BtnPopupClose' href='#'></a>";
        }
        var doTtmpl = doT.template(template);
		//判断页面是否采用了绝对剧中布局，需要特殊处理，如Consumption页面
		//data.isAbsoluteCenter参数必须为数组,[是or否,用jquery取到的绝对居中的元素]
		if(data.isAbsoluteCenter && $.type(data.isAbsoluteCenter)=="array" && data.isAbsoluteCenter[0]==true){
			var mainBodyHeight = mainBody.height();
			var mainBodyWidth = mainBody.width();
			var absObjct = data.isAbsoluteCenter[1];
			var absObjctHeight = absObjct.height();
			var absObjctWidth = absObjct.width();
		}
        //绑定弹出层
        var that = this;
        $(target).off().on(evt, ele, function (event, trigger) {
			var $this = $(this);
			if(data.parent){
				if(data.parent ===true){
					$this = $(this).parent();	
				} else {
					$this = $(this).closest(data.parent);
				}
			};
			if(data.fn && $.type(data.fn) == "function"){
				data.fn($this);
                return false;
            }
            if (!$(target)[0] || !popup) {
                return false;
            }
            if ($this.hasClass("off")) {
                return;
            }
            var index = $this.index();
            var interval = 0;
            if (data.alarm === true) {
                interval = 100;
            } else {
                if (evt != "click") {
                    interval = 500;
                }
		if(data.interval){
			interval = data.interval;
		}
            }
            if (that.PopTimer != null) {
                clearTimeout(that.PopTimer);
            };
            data.index = index;
            data = $.extend(true, {}, data, {
                "dataIndex": $(this).attr("index"),
                "dataKey": $(this).attr("name")
            });
	    $.extend(true,Configs.Popup.Data,data);
            popup.html(doTtmpl(data));
            that.PopTimer = setTimeout(function () {
                doShow();
            }, interval);
            function doShow() {
                if (data.close === true) {
					var BtnClosePopup = popup.find("#BtnPopupClose");
					that.PopupClose(popup,BtnClosePopup);
                }
                Configs.Popup.index = index;
                Configs.Popup.status = true;
                var PopupContent = popup.find("div.popup-content");
                var PopupAlarm = popup.find("div.alarm-popup");
                var PopupWidth = popup.outerWidth(true);
                var PopupHeight = popup.outerHeight(true);
                var thisWidth = $this.width();
                var thisLeft = $this.position().left;
                var thisTop = $this.position().top+10;
                var thisHeight = $this.outerHeight(true);
				var mainScrollTop = mainBody.scrollTop();
                var top = thisTop - PopupHeight + mainScrollTop;
                if (data.alarm) {
                    top = thisTop - PopupHeight;
                    //两行的时候，靠左对齐
                    PopupContent.css("text-align", PopupHeight > 90 ? "left" : "center");
                    PopupAlarm.css("text-align", PopupHeight > 90 ? "left" : "center");
                }
				if(data.isAbsoluteCenter){
					var w = mainBodyWidth/2-absObjctWidth/2;
					thisLeft = thisLeft+w;
					var parent = $this.parent();
					var isCenter = ($this.parent().attr("iscenter")==1) && mainBody[0] && absObjct[0];
					if(isCenter){
						var h = mainBodyHeight/2-absObjctHeight/2;
						thisTop = thisTop+h;
					}
				};
                var arrow = popup.find("div.popup-arrow");
                var maxtop = popup.height();
                var arrowTop = popup.find("div.popup-arrow-top");
                if (thisTop - maxtop-mainScrollTop < 0) {
					Configs.Popup.Arrow = "top";
                    if (arrowTop.length > 0) {
                        top = top + thisHeight + maxtop+(isCenter? 2 : 7)- mainScrollTop;
                        arrow.remove();
                        arrow = arrowTop;
                        arrow.show();
						if(BtnClosePopup){
							BtnClosePopup.removeClass("popup-close-b").addClass("popup-close-t");
						}
                    }
                } else {
					Configs.Popup.Arrow = "bottom";
                    arrowTop.remove();
                    if (arrowTop.length > 0) {
                        top -= (isCenter ? 7 : -10 +mainScrollTop);
                    }
					if(BtnClosePopup){
						BtnClosePopup.removeClass("popup-close-t").addClass("popup-close-b");
					}
                }
                var arrowWidth = arrow.width();
                var arrowLeft = function (n) {
                    return Math.floor(thisLeft - n + (thisWidth - arrowWidth) / 2)
                };
                var left = thisLeft - (PopupWidth - thisWidth) / 2;
                var maxr = data["maxr"] ? (Number(data["maxr"])<767 ? 767 :Number(data["maxr"])) : 767;
                if (data.system) {
                    left = 5;
                } else if (left < 0) {
                    left = 1;
                } else if (left + PopupWidth > maxr) {
                    left = maxr - PopupWidth;
                }
                var deviceindex=index+1;
                if(jQuery.cookie("systeminfo")==1){
                    if(deviceindex%4==0){
                        left=left+100;
                    }
                }else{
                    if(deviceindex%5==0||(deviceindex+1)%5==0){
                        left=left+300;
                    }
                }
                popup.css({ "top": top+(isCenter? h: 0), "left": left}).show();
                if (!data.alarm) {
                    arrow.css({ "margin-left": arrowLeft(left)});
                }
				arrow.css({"visibility":"visible"});
				//缓存弹出层的一些值;
				Configs.Popup.Style = [popup.attr("style")];
				Configs.Popup.Style.push(arrow.attr("style"));
				if(data.close === true && BtnClosePopup[0]){
					Configs.Popup.CloseHtml = BtnClosePopup[0].outerHTML;
				}
            };
			return false;
        }).on("mouseleave", ele, function () {
            if (data.hide) {
                popup.hide();
                Configs.Popup.index = null;
                Configs.Popup.status = false;
                if (that.PopTimer) {
                    clearTimeout(that.PopTimer);
                }
            }
        })
		if(popup && popup[0]){
			popup.off().on("mouseenter", function () {
				that.SystemPop = false;
			}).on("mouseleave", function () {
				if (data.hide) {
					$(this).hide();
				}
				that.SystemPop = true;
			});
		}					
    },
	PopupClose:function(popup,BtnClosePopup){
		var BtnPopupClose = BtnClosePopup? BtnClosePopup : $(popup).find("#BtnPopupClose");
		if(BtnPopupClose[0]){
			BtnPopupClose.off().one("click", function () {
				$(popup).hide();
				Configs.Popup.index = null;
				Configs.Popup.status = false;
				return false;
			});
		};
	},
    SystemPop: true,
    /*---------------------------------*
    * rectifier、converter、solar、battery等页面绘制电流电压表的集成方法
    * 参数： target->目标(一般为ID)，data->数据
    *---------------------------------*/
    SystemDrawMeter: function (target, data) {
        //绘制电流电压表组成数据
        var meterDatas = {
            center: [165, 135],
            background: {
                radius1: 56,
                radius2: 45
            },
            finger: {
                angle: [180, 30],
                width: [11, 20],
                radius: 46
            },
            alarm: {
                outer: {
                    value: data.data.group.chart["value_alarm"],
                    color: ["#a2ee00", "#ffae00", "#e35500"],
                    radius: 90
                },
                inner: {
                    value: [0, 70, 85, 120],
                    radius: 52
                }
            },
            value: {
                outer: data.data.group.chart['used_cap'],
                inner: data.data.group.chart['volt'],
                innerA: data.data.group.chart['curr'],
                toFix: [0],
                unit: ["%"]
            }
        };
        //调用Chart对象方法drawMeter绘制图表
        Chart.drawMeter(target, meterDatas);
    },
    //系统模块页面共用回调函数
    SystemCommon: function (data) {
		var mainBody = $("#mainBody");
		if ($("a.system_set_btn").length > 0) {
            $("div.system-list>ul>li").off().on("mouseenter", function () {
                if ($(this).hasClass("off")) { return false; }
                $(this).find("a.system_set_btn").show();
            }).on("mouseleave", function () {
                $(this).find("a.system_set_btn").hide();
            });
        };
        var that = this;
        if (that.SystemSroll > 0) {
            setTimeout(function () {
                mainBody.scrollTop(that.SystemSroll);
                that.SystemSroll = 0;
            }, 1);
        };
        /*遍历headline*/
        var operation = [];
        for (var h = 0, hlen = data.data.headline.length; h < hlen; h++) {
            var itemlen = data.data.headline[h].length;
            operation[h] = data.data.headline[h][itemlen - 2] + "-" + data.data.headline[h][itemlen - 1];
        };
		/*显示设置列表*/
		var list = $("div.system-list,div.system-summary");
		var detail = $("#SystemDetail");
        //绑定弹出层
		Configs.Popup.Data = {
            headline: data.data['headline'],
            operation: operation,
            single_data: data.data['single_data'],
            system: true,
			close:true
        }
        this.PopupInfo("div.system-list", "click", "li", ["#popup"], Configs.Popup.Data);
		this.PopupClose("#popup");
		//绑定详细设置按钮
		$("#closeDetail").off().on("click", function () {
			$("#mainTab>a.currentMenu").click();
			return false;
		});
		$("div.system-list>ul").off().on("click", "a.system_set_btn", function(){
			var $this = $(this).parent();
			that.SystemSroll = mainBody.scrollTop();
			detail.show();
			list.hide();
			Control.GetTemplate(jQuery.evalJSON($this.find("a.system_set_btn").attr("data").replace("{,", "{")));
			return false;
        });
    },
    SystemSroll: 0,
    /*设置Setting日期*/
    SetSettingDate: function (seconds) {
        var setTime = new Date(1000 * (seconds + Configs.timezone * 3600));
        var setTimeStr = setTime.getFullYear() + "-" + Validates.MakeupZero(setTime.getMonth() + 1) + "-" + Validates.MakeupZero(setTime.getDate()) + " " + Validates.MakeupZero(setTime.getHours()) + ":" + Validates.MakeupZero(setTime.getMinutes()) + ":" + Validates.MakeupZero(setTime.getSeconds());
        return setTimeStr;
    },
    //倒计时程序,可能也会用在非重启的功能上
    //restart，是否需要重启，默认为重启,设置为false,可取消重启，只是倒计时
    //time, 倒计时时间,单位 "秒"
    //text,非重启状态，需要提示的文字
    //fn, 倒计时完成时需要执行的回调函数
    DoRestart: function (restart, time, text, fn) {
        var that = this;
        var NeedRestart = (restart === false) ? false : true;
        if (NeedRestart) {
            jQuery.cookie("restart", "1", { path: "/" });
            Control.StopKeepLogin();
            Control.StopPollingAlarm();
            Control.StopPolling();
        };
        var RestartTimes = (time && $.type(time) == "number") ? time : Configs.RestartTime;
        var Tips = $("#SetProgress"), TipsEm = Tips.find("em").eq(0);
        if (NeedRestart) {
            TipsEm.html(Language.Html["041"] + " <span id='TimerCount'>" + RestartTimes + "</span>" + Language.Html["042"] + Language.Html["054"]);
        } else {
            TipsEm.html((text ? text : "") + " <span id='TimerCount'>" + RestartTimes + "</span>" + Language.Html["042"]);
        }
        that.SetProcessPosition();
        var RestartNow = false;
        TimerAction();
        var RestartXHR = null;
		var TimerCount = $("#TimerCount");
		var minWait = 0;//防止立刻返回登录页，设置至少等待时间15秒
        function TimerAction() {
            if (NeedRestart && RestartTimes >0 && RestartTimes % 5 == 0 && minWait >15) {
                if (RestartXHR) { RestartXHR.abort(); RestartXHR = null; }
                RestartXHR = $.ajax({
                    url: "/var/datas/data.login.html?_=" + new Date().getTime(),
                    timeout: Configs.Data.timeout,
                    success: function (data, textStatus, jqXHR) {
                        var re = new RegExp("\"%__data_end__%\"", 'g');
                        if (re.test(data)) {
                            data = data.replace("\"%__data_end__%\"", "");
                            try {
                                var data = jQuery.evalJSON(data);
                                RestartNow = true;
                            } catch (e) { }
                        }
                    }
                }).always(function (jqXHR, textStatus, errorThrown) {
                    jqXHR = null;
                    textStatus = null;
                    errorThrown = null;
                    RestartXHR = null;
                });
            };
            var Timer = setTimeout(function () {
                RestartTimes--;
				minWait++;
                if (RestartTimes == 0 || RestartNow === true) {
                    clearTimeout(Timer);
                    if ($.type(fn) == "function") {
                        fn();
                    }
                    if (NeedRestart) {
                        TipsEm.html(Language.Html["043"]);
                        location.href = Configs.login+"?"+new Date().getTime();
                    }
                    that.SetProcessPosition();
                } else {
                    TimerCount.html(RestartTimes);
                    TimerAction();
                }
            }, 1000);
        };
    },
    /*---------------------------------*
    * 弹出设置"过程"显示框
    *---------------------------------*/
    SetProcess: function (text, close, cla,callback) {
        Configs.Backspace = false;
        var that = this;
        var c = (close === false) ? close : true;
        var c_html = "";
        if (c) {
            c_html = Configs.Prompt.cancel;
        }
        Control.PromptEvent.Cover();
        $("div.SetProgress").remove();
        $("body").append("<div class='SetProgress" + (cla ? " " + cla : "") + "' id='SetProgress'><div class='SetProgressContent' id='SetProgressContent'><em>" + text + "</em>" + c_html + "</div></div>");
        if (c) {
            var CloseButton = $("#SetProgress").find("a.close");
            CloseButton.one("click", function () {
                that.SetProcessRemove();
				if ($.type(callback) == "function") {
					callback();
				}
            })
        }
        this.SetProcessPosition();
		return this;
    },
    SetProcessPosition: function () {
        var SetProgress = $("#SetProgress");
        var width = SetProgress.innerWidth();
        var siderwidth = 96;
        if(jQuery.cookie("systeminfo")==1){
            siderwidth=siderwidth-239;
        }
        SetProgress.css({ "margin-left": (-width + siderwidth) / 2 });
    },
    /*---------------------------------*
    * 移除设置弹出框
    *---------------------------------*/
    SetProcessRemove: function () {
        Control.RemoveFrames();
        var cover = $("#PromptCover"), loading = $("#SetProgress");
        cover.remove();
        loading.remove();
    },
    /*---------------------------------*
    * 设置过程的“开始”阶段
    *---------------------------------*/
    SetProcessStart: function () {
        $("#SetProgress").find("em").html(Language.Html['011']);
    },
	GetProcess: function(){
		var doc = document;
		var SetProgress = doc.getElementById("SetProgress");
		if(!SetProgress){
			this.SetProcess("");
			SetProgress = doc.getElementById("SetProgress");
		};
		return $(SetProgress);
	},
    /*---------------------------------*
    * 设置过程的“结束”阶段
    *---------------------------------*/
    SetProcessDone: function (text, callback, data) {
        var that = this;
        var SetProgress = this.GetProcess();
        var Error = SetProgress.find("em");
        Error.html(text);
        if ($.type(callback) == "function") {
            Error.append(Configs.Prompt.retry);
        }
        SetProgress.find("a").css("display", "inline-block");
        this.SetProcessPosition();
        var Retry = SetProgress.find("a.resetSendSubmit");
        Retry.one("click", function () {
            if ($.type(callback) == "function") {
                if (data) {
                    callback(data);
                } else {
                    callback();
                }
                that.SetProcessPosition();
            };
        });
    },
    /*---------------------------------*
    * 设置过程的“OK”阶段
    *---------------------------------*/
    SetProcessOK: function (text, interval) {
        var SetProgress = this.GetProcess();
        var Error = SetProgress.find("em");
        var Btn = SetProgress.find("a");
        var isIE6 = /IE6/g.test(Configs.Browser);
        Error.html(text);
        Btn.remove();
        var Cover = $("#PromptCover");
		if (isIE6) {
            Cover.css({ "opacity": 0 });
        } else {
            Cover.remove();
        }
        //SetProgress.css({ "padding": 0 });
        if (!interval) { var interval = 500; }
        setTimeout(function () {
            SetProgress.fadeOut(500, function () {
                SetProgress.remove();
                if (isIE6) {
                    Cover.remove();
                };
            });
        }, interval);
        this.SetProcessPosition();    
    },
	/* 设置表格表头浮动
	 * 表格外边必须有一个<div>层,mainBody层除外.如system inventory页面
	 * tableid ->表格ID
	 * createid->创建的动态层的id
	 * scroll ->mainBody滚动的高度,如果是doucment滚动，sroll设为0
	 * initTop->初始化距离网页最顶端高度
	*/
	FixThead: function(tableid,createid,scroll,initTop){
		//不支持IE6,IE7,IE8，IE6完全不支持position:fixed属性;IE7,IE8支持的不是很好,实现起来会产生问题，所以屏蔽了这三个浏览器
		if(/IE6|IE7|IE8/g.test(Configs.Browser)){ return false; }
		var doc = document,target = $(doc.getElementById(tableid));
		if(!target[0]){ return false; }
		var isHas = doc.getElementById(createid);
		if(isHas){ 
			var fixed = $(isHas);
		} else {
			var table = $(doc.createElement("table")),
				header = target.find("thead").eq(0).clone(),
				fixed = $(doc.createElement("div"));
			table.attr({"border":0,"cellspacing":0,"cellpadding":0,"class":target[0].className}).css({"border-top":"none"}).html(header);
			fixed.attr({"id":createid,"class":"table-thead"}).html(table);
		};
		var offset = target.offset(),
			left = offset.left,
			top = offset.top,
			scroll2 = target.parent().position().top+scroll,
			initTop = initTop ? initTop : 166,
			scrollLeft = $(doc).scrollLeft();
		if(scroll>scroll2){
			fixed.css({"left":left-scrollLeft,"top":initTop-Configs.bodyScroll}).insertBefore(target).show();
		} else {
			fixed.hide();
		}
	},
	/*
	 * 移动光标到文字的末尾
	 */
	moveCursorToEnd: function(el) {
		el.focus();
		if (typeof el.selectionStart == "number") {
			el.selectionStart = el.selectionEnd = el.value.length;
		} else if (typeof el.createTextRange != "undefined") {
			var range = el.createTextRange();
			range.collapse(false);
			range.select();
		}
		return $(el);
	}
};