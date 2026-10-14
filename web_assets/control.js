/*!
 * Author: Jerman.Xie | xieguishi@126.com
 * Date: 2013.09
 * 
 * 控制器：
 * 控制是否向服务器发送异步请求,并获取数据
 * 控制渲染数据到页面
 * 控制错误提示
 */
var Control = {
    //判断是否是轮询的请求
    isPolling: false,
    //判断alarm请求是否是轮询
    isAlarmPolling: false,
    //判断trend请求是否是轮询
    isTrendPolling: false,
    //轮询数据
    polling: null,
    //数据信息头中返回的Etag值
    dataEtag: null,
    //模板信息头中返回的Etag值
    templateEtag: null,
    //alarm数据返回的Etag值
    alarmEtag: null,
    //trend数据返回的Etag值
    trendEtag: null,
	//检测登录状态
    CheckLogin: function () {
        var name = jQuery.cookie("user_name");
        if (!name || name == "" || name == "null") {
            alert(Language.Html['019']);
            location.href = Configs.login;
            return false;
        }
        return true;
    },
	//判断是否为重启状态，是的话返回登录页面
	CheckReLogin:function(){
		if (jQuery.cookie("restart") == "1") {
            location.href = Configs.login;
            return false;
        }
		return true;
	},
	//刷新当前页面
    RefreshModule: function (re) {
		if(re===false){
			return false;
		} else {
			if($.type(re)=="array" && re[0]==true && $.type(re[1])=="function"){
				re[1]();
				return false;
			}
		};
        this.CheckReLogin();
        if (Configs.Data.failNum != 0) { Configs.Data.failNum = 0; }
        //清除cover层
        var PromptCover = document.getElementById("PromptCover");
        if (PromptCover && !document.getElementById("SetProgress")) { $(PromptCover).remove(); }
        this.GetTemplate(Configs.Template.info,true);
    },
	//退出登录
    LoginOut: function (url) {
        var clearCookies = Configs.Cookies.names;
        for (var i = 0, ilen = clearCookies.length; i < ilen; i++) {
            jQuery.removeCookie(clearCookies[i], "");
        }
        if (url) {
            location.href = url;
        } else {
            location.href = Configs.login;
        }
    },
    /*=========================================*
    * Prompt函数改进版
    * loading及错误信息显示函数
    * 优化alert,confirm事件
    * 加入弹出层
    *=========================================*/
    PromptEvent: {
        //把传入进来的ID号字符串，DOM转换成jQuery对象
        GetElement: function (target) {
            var type = $.type(target);
            switch (type) {
                case "string":
                    return $("#" + target.replace("#", ""));
                case "object":
                    return $(target);
                default:
                    return false;
            };
        },
        CheckObj: function (args) {
            if (!$.type(args) == "object") {
                return false;
            }
            return true;
        },
        /*
        * 设置child相对parent水平居中，垂直相对距离根据args["marginTop"]来确定
        * args["interval"]参数，用来延时抓取parent的offset，以便正确定位
        * parent ->相对的目标div
        * child  ->需要居中定位的div
        */
        ResetStatus: null,
        ResetEle: function (parent, child, args) {
            if (args["reset"]) {
                parent = $("#" + parent);
            }
            var interval = args["interval"];
            if ($.type(interval) == "number" && interval >= 0) {
                setTimeout(function () {
                    SetPosition();
                }, args["interval"]);
            } else {
                SetPosition();
            }
            this.ResetStatus = args["marginTop"];
            function SetPosition() {
                if (!child) { return false; }
                var $child = $(child);
                var child_width = $child.innerWidth();
                var target_width;// = parent.innerWidth();
                if(jQuery.cookie("systeminfo")==0){
                    target_width=1163;
                }else{
                    target_width=917;
                }
                var offset = parent.offset();
                if (!offset) { return; }
                var top = offset.top;
                var marginTop = args["marginTop"];
                var left = (target_width - child_width) / 2;
                if (marginTop == "center") {
                    top = (parent.height() - $child.height()) / 2;
                } else {
			if($.type(marginTop) == "number"){
				top = marginTop-35;
			} else {
				var ph = parent.height();
				var ch = $child.height();
				if(ph>70*2){
					top = 70;	
				} else if(ph>ch+10 && ph<70*2) {
					top = (ph - ch)/2;
				} else {
					top = 0;
				}
			}
                }
                $child.css({ "left": left, "top": top }).show();
            };
        },
        Remove: function (args) {
            this.LoadingRemove(args);
            this.TipRemove(args);
        },
        /*
        * Loading,加载数据loading进度条,调用Loading时一定要匹配调用它Loading({remove:"相对的target值"})使用;
        * args ->参数对象，包含target,html,Class,marginTop
        * target -> 滚动条加载到哪个模块上,传一个ID号(带#或不带#)或DOM对象
        * html   -> loading里面需要显示的html代码
        * Class  -> loading 可能要添加的class样式,不同的样式会展示不同的进度条
        * reset  -> 如果为true，则重新定位loading的相对位置
        * clear  -> 是否需要清除target的内容,设为false时不清除target的内容
        * remove -> 传递生成loading时的target值
        * interval ->是否需要延迟显示，interval为数字，且大于或等于0则生效
        * append   ->为true时表示从target后面追加元素
        */
        LoadingData: {},
        LoadingStatus: false,
        LoadingRemove: function (args) {
            var id_prefix = "#PromptLoading_";
            var remove = args["remove"];
            if (remove && $.type(remove) == "string") {
                var target = $(id_prefix + remove);
                if (target) {
                    target.remove();
                    delete this.LoadingData[remove];
                    this.LoadingStatus = "removed";
                }
            };
        },
        Loading: function (args) {
            this.LoadingStatus = "created";
            //loading默认样式
            var loadingClass = "PromptLoading2";
            var id_prefix = "PromptLoading_";
            if (!this.CheckObj(args)) { return; };
            //避免重复生成
            if (document.getElementById(id_prefix + args["target"])) { return; };
            //reset
            if (args["reset"] == true) {
                var loadingdata = this.LoadingData;
                if (loadingdata) {
                    for (var item in loadingdata) {

                        this.ResetEle(loadingdata[item]["target"], loadingdata[item]["loading"], args);
                    }
                };
                return;
            };
            //remove
            this.LoadingRemove({ remove: args["remove"], id_prefix: id_prefix });
            if (this.LoadingStatus == "removed") { return false; }
            //把target转换成jQuery DOM对象
            var target = this.GetElement(args["target"]);
            if (!target[0]) { return false; }
            var target_id = target[0].id;



            //1、清空target的内容,默认是清除
            var clear = (args["clear"] === false) ? args["clear"] : true;
            if (clear) {
                target[0].innerHTML = "";
            }
            //2、body后面添加loading,并以target的相对位置居中
            var loading = document.createElement("div");
            $(loading).attr("id", id_prefix + target_id);
            //默认生成在target里面,避免每次生成loading都要在生成后清除loading
            target[0].appendChild(loading);
            this.LoadingData[target_id] = { target: target_id, loading: loading };
            //添加默认样式
            var Class = args["Class"];
            if (Class && $.type(Class) == "string") {
                loadingClass += " " + Class;
            };
            loading.className = loadingClass;
            //添加loading内容
            var html = args["html"];
            loading.innerHTML = "<img src='../images/update_loading.gif'>" + (html ? html : Language.Html["013"]);

            //3、获取target的位置，设置loading相对target水平居中
            this.ResetEle(target, loading, args);
        },
        /*
        * Tip: 
        * 提示错误，在目标target生成，并相对居中，如果有loading,同时清除loading
        * target -> 出现错误的目标区域
        * text   -> 错误提示内容
        * img    -> 告警提示图片
        * marginTop ->距离顶边的距离,center为垂直居中
        * clear  -> 清空目标div,再写入提示信息
        */
        TipRemove: function (args) {
		var target = $("#PromptTip_" + args["remove"]);
		if(target[0]){
			target.remove();
		}
        },
        Tip: function (args) {
            if (!this.CheckObj(args)) { return; };
            var target = this.GetElement(args["target"]);
            if (!target[0]) { return false; }
            var target_id = target[0].id;
            //清除loading
            this.LoadingRemove({ remove: target_id });
            var TipClass = "PromptTip";
            //添加自定义样式
            var Class = args["Class"];
            if (Class && $.type(Class) == "string") {
                TipClass += " " + Class;
            };
            var Tip = document.getElementById("PromptTip_" + target_id);
            if (Tip) {
                $(Tip).remove();
            }
            Tip = document.createElement("div");
            $(Tip).attr("id", "PromptTip_" + target_id);
            Tip.className = TipClass;
            var TipContent = document.createElement("div");
            TipContent.className = "PromptTipContent";
            //是否需要清除目标target的内容,默认不清除
            var clear = args["clear"] === true ? args["clear"] : false;
            if (clear) {
                target[0].innerHTML = "";
            }
            //添加内容到TipContent
            var text = args["text"];
            var ErrorImgURL = (args["img"] && args["img"] != "") ? args["img"] : '../images/error.gif';
            TipContent.innerHTML = text && text != "" ? text : Language.Html["038"];
            Tip.appendChild(TipContent);
            Tip.style.visibility = "hidden";
            target[0].appendChild(Tip);
            this.ResetEle(target, Tip, args);
            Tip.style.visibility = "visible";
        },
        //弹出告警
        Alert: function (text) {
            if (!text) { return false; };
            var html = "<div class='PromptAlertContent'><img src='../images/error.gif'>" + text + "</div><div class='PromptAlertButton'><a href='#'>" + Language.Html["015"] + "</a></div>";
            this.Pop({ title: Language.Html["039"], Class: "PromptAlert", fn: t, html: html });
            var that = this;
            function t(data, pop, cover) {
                var width = $(pop).find("div.PromptAlertContent").innerWidth() + 40;
                $(pop).css({ "width": width, "margin-left": "-" + width / 2 + "px" });
                var button = $(pop).find("div.PromptAlertButton>a");
                button.focus();
                button.one("click", function () {
                    that.PopClose(pop, cover);
                    return false;
                });
                $(pop).css("visibility", "visible")
            }
			return false;
        },
        /*
        cover:相对body对象 生成一个遮蔽层
        opacity->透明度
        backgroundColor-> 遮蔽层的颜色
        target->windows reset时才传递此参数
        */
        Cover: function (args) {
            //判断遮蔽层是否已经存在了，存在了则显示它，不再生成
	    var getCover = document.getElementById("PromptCover");
            var HasCover = (args && args["target"]) ? args["target"] : getCover;
            if (HasCover || getCover) {
                SetCover(HasCover);
                $(HasCover).show();
                return getCover;
            }
            var opacity = 0.3;
            var backgroundColor = "#000";
            if (args && this.CheckObj(args)) {
                if (args && args["opacity"]) {
                    opacity = args["opacity"];
                };
                if (args["backgroundColor"]) {
                    backgroundColor = args["backgroundColor"];
                };
            };
            var cover = document.createElement("div");
            cover.id = "PromptCover";
            cover.className = "PromptCover";
            SetCover(cover);
            function SetCover(target) {
                if (!$(target)[0]) {
                    target = document.getElementById("PromptCover");
                };
                var body = $("body");
                var width = body.innerWidth();
                var height = body.innerHeight();
                if (/IE6/g.test(Configs.Browser)) {
                    target.innerHTML = "<iframe width='" + width + "px' height='" + height + "px' frameborder='0' scrolling='no' marginheight='0' marginwidth='0' src='about:blank'></iframe>"
                }
                $(target).css({ "width": width, "height": height, opacity: opacity, "background-color": backgroundColor });
            }
            $("body").append(cover);
            return cover;
        },
        /*
		* cover ->是否使用屏蔽层
        * title ->弹出层的标题
        * fn    ->需要调用的回调函数
        * html  ->需要显示的内容，这内容当然你也可以在回调函数里设置
        * data  ->传递给回调的数据
        */
        Pop: function (args) {
            if (!this.CheckObj(args)) { return; };
	    //运行回调
	    function callFun(){
	    	if ($.type(args["fn"]) == "function") {
	    		if (args["Class"] == "PromptAlert") {
	    			$(pop).css("visibility", "hidden");
	    		};
	    		args["fn"](args["data"], pop, cover);
	    	};
	    }
	    if(document.getElementById("PromptPop")){ 
	    	callFun(); 
	    	return false;
	    }
            var body = $("body");
            var ScrollTop = $(window).scrollTop();
            //生成一个遮蔽层,默认为true
            args["cover"] = (args["cover"] === false) ? args["cover"] : true;
            var cover = this.Cover(args);
            //生成pop层结构
            var oFrag = document.createDocumentFragment();
            var pop = document.createElement("div");
            pop.id = "PromptPop";
            var popClass = "PromptPop";
            //添加自定义样式
            var Class = args["Class"];
            if (Class && $.type(Class) == "string") {
                popClass += " " + Class;
            };
            pop.className = popClass;

            var pop_title = document.createElement("div");
            pop_title.id = "PromptPopTitle";
            pop_title.className = "PromptPopTitle";
            var titleHTML = "";
            if (args["title"] && args["title"] != "") {
                titleHTML += args["title"];
            }
            pop_title.innerHTML = "<span>" + titleHTML + "</span><a href='#' id='PromptPopClose' class='PromptPopClose'></a>";
            oFrag.appendChild(pop_title);
            var pop_content = document.createElement("div");
            pop_content.id = "PromptPopContent";
            pop_content.className = "PromptPopContent";
            if (args["html"]) {
                pop_content.innerHTML = args["html"];
            }

            oFrag.appendChild(pop_content);
            pop.appendChild(oFrag);
            body.append(pop);
            $(pop).show();
	    callFun();
            //绑定一次，删除弹出层
            var that = this;
            $("#PromptPopClose").one("click", function () {
                that.PopClose(pop, cover);
                return false;
            });
        },
        PopClose: function (pop, cover) {
            Control.RemoveFrames();
            $(pop).remove();
            $(cover).remove();
        }
    },
    /*---------------------------------*
    * 获取"模板"数据(字符串)
    *---------------------------------*/
	ReGetData:null,
    ClickStart: 0,
    GetTemplate: function (args,refresh) {
		this.CheckReLogin();
		//重置Configs.refresh
		Configs.refresh = false;
        //解除Rectifier页面弹出层状态
        var SetProgress = document.getElementById("SetProgress");
        Configs.Popup.status = false;
		if(SetProgress && !refresh){ return false; }
        if ((this.ClickStart != 0 || SetProgress) && args["clickfast"] !== false) {
            if (new Date().getTime() - this.ClickStart < Configs.ClickInterval) {
                if (SetProgress) { $(SetProgress).remove(); }
                //提示单击过快，再自动隐藏
                Pages.SetProcess(Language.Html["033"], null, "ClickTooFast");
                Pages.SetProcessOK(Language.Html["033"], 500);
                this.ClickStart = new Date().getTime();
                return false;
            }
        }
        this.ClickStart = new Date().getTime();
		
		//20秒之后，如果发现loading还在进行，手动进行一次刷新
		if(this.ReGetData){ clearTimeout(this.ReGetData); };
		this.ReGetData = setTimeout(function(){
			var content = $("#mainContent");
			if(content[0]){
				if(content.find("div.PromptLoading2").length>0){
					that.RefreshModule();
				}
			}
		},20000);

		//判断是否自定义超时时间，默认为5秒
		Configs.Data.timeout = (args.timeout && $.type(args.timeout) == "number") ? args.timeout : Configs.Data.defaultTimeout;
		

        //如果非首页,则停止Trend轮询
        if (Configs.isHomePage(args["fn"])) {
            Control.StopPollingTrend();
        } else {
            if (!Control.isPolling) {
                if (Configs.ClickHomeNum > Configs.ClickHomeMax) {
                    window.location.reload();
                    return false;
                }
            }
        }
        var that = this;
        //检查是否登录
        if (!this.CheckLogin()) {
            return false;
        }
        if (Configs.Alarm.expand) {
            Control.SetLayout();
            Configs.Alarm.expand = false;
        }
        this.StopPolling();
        //请求模板地址不存在，则返回
        if (!args["template"]) {
            alert(Language.Html['003']);
            return;
        }
        if (that.SettingOtherXHR || that.SettingOtherXHR != null) {
            that.SettingOtherXHR.abort();
        };
        if (that.DataXHR || that.DataXHR != null) {
            that.DataXHR.abort();
            Configs.Data.failNum = 0;
        }
        if (that.TemplateXHR || that.TemplateXHR != null) {
            that.TemplateXHR.abort();
        }
		//定位当前栏目
		Control.SetNavigation(args);
        //menuIndex=>导航标识符
        var menuIndex = Number(args['menuIndex']);
        var getTemplates = [];
        if (/,/g.test(args["template"])) {
            getTemplates = args["template"].split(",");
        };
        var getTemplatesLength = getTemplates.length;
        var getUrlTimes = 0;
        function loopGet(time) {
            if (getTemplatesLength > 0) {
                if (time < getTemplatesLength) {
                    var requireURL = getTemplates[time];
                    if (/:/g.test(requireURL)) {
                        var requireSigns = requireURL.split(":");
                        get(requireSigns[1], requireSigns[0])
                    } else {
                        get(requireURL)
                    }
                }
            } else {
                get(args["template"]);
            };
        }
        loopGet(0)
        function get(url, templateSign) {
            that.TemplateXHR = $.ajax({
                timeout: Configs.Data.timeout,
                dataType: "html",
                //headers : {"If-None-Match":that.templateEtag},  //模板不要加Etag,每次都请求，解决模板重用！！！
                cache: true,
                url: url,// + "?_=" + new Date().getTime(),
                beforeSend: function () {
                    var currentModules = document.getElementById(args["modules"]);
                    if (currentModules) {
                        //初始化模块为空,写入loading
                        $(currentModules).children().off().html("");
                        that.PromptEvent.Loading({ target: currentModules});
                    }
                    //获取模板数据
                    if (args) {                     
                        if ($.type(args['modules']) == 'string') {
                            Configs.Modules.Renders = [];
                            if (/,/g.test(args['modules'])) {
                                Configs.Modules.Renders = $.extend(true, {}, Configs.Modules.Renders, args['modules'].split(','));
                            } else {
                                Configs.Modules.Renders.push(args['modules']);
                            }
                        } else {
                            Configs.Modules.Renders = $.extend(true, {}, Configs.Modules.Renders, args['modules']);
                        }
                    };
                },
                success: function (data, textStatus, jqXHR) {
                    if (Configs.isHomePage(args["fn"])) {
                        Configs.HomePage = true;
                    } else {
                        Configs.HomePage = false;
                    }
                    that.isPolling = false;
                    if (jqXHR.status == 200) {
                        //依次获取args["template"]中的模板
                        if (getUrlTimes < getTemplatesLength - 1) {
                            if (templateSign) {
                                Configs.Template.common.push([templateSign, data]);
                            } else {
                                Configs.Template.common.push(data);
                            }
                            getUrlTimes++;
                            loopGet(getUrlTimes);
                            return;
                        } else {
                            that.templateEtag = jqXHR.getResponseHeader("Etag");
                            //请求成功才缓存数据,否则保持上次数据不变
                            if (data) {
                                var modules = Configs.Modules.Renders;
                                if (modules.length == 1) {
                                    var commonHTML = Configs.Template.common;
                                    for (t = 0, tlen = commonHTML.length; t < tlen; t++) {
                                        if (commonHTML[t] instanceof Array) {
                                            var tmpReg = new RegExp(commonHTML[t][0], "g");
                                            if (tmpReg.test(data)) {
                                                data = data.replace(tmpReg, commonHTML[t][1]);
                                            } else {
                                                data = commonHTML[t][1] + data;
                                            }
                                        } else {
                                            data = commonHTML[t] + data;
                                        }
                                    };
                                    Configs.Template.content[modules[0]] = data;
                                    //应用即删除
                                    Configs.Template.common = [];
                                    gettime = 0;
                                } else {
                                    //同时获取多个模块的数据在此处理	
                                }
                            } else {
                                var innerTemplate = document.getElementById(args["template"]);
                                Configs.Template.content['mainContent'] = innerTemplate ? innerTemplate.innerHTML : "";
                            };
                        };
                    }
                    //存储templateInfo信息
                    Configs.Template.info = args;
                    Configs.MainScrollHeight = 0;
                    if (!args['data']) {
                        that.RenderData();
                        return;
                    }
                    if (menuIndex == 0 || menuIndex == 1 || (menuIndex == 2 && args['data'])) {
                        if (args['data']) {
                            that.GetData();
                        } else {
                            that.RenderData();
                        }
                    } else if (menuIndex == 2 && !args['data']) {
                        //当menuIndex==2时，表示是二级菜单，不需要重新获取数据，直接从父级取数据就OK了
                        //取得数据,并渲染页面
                        if (jqXHR.status == 200) {
                            Configs.Template.content[args['name']] = data;
                        }
                        that.RenderData();
                    }
                },
                error: function (data, textStatus) {
                    if (textStatus == "abort") {
                        that.TemplateXHR = null;
                        return false;
                    }
                    switch (data.status) {
                        case 404:
							if (Configs.isHomePage(args["fn"])) {
								setTimeout(function(){
									location.reload();
								},3000)
							} else {	
								that.PromptEvent.Tip({ target: args["modules"], text: Language.Html['003'] + Configs.Prompt.refresh });
							}
                            break;
                    };
                    //请求当前模板失败,则继续轮询上一页面数据
                    that.StartPolling();
                }
            }).always(function (jqXHR, textStatus, errorThrown) {
                jqXHR = null;
                textStatus = null;
                errorThrown = null;
                that.TemplateXHR = null;
            })
        };
    },
    //轮询数据
    StartPolling: function (args) {
        var that = this;
        if (that.DataXHR || that.DataXHR != null) {
            that.DataXHR.abort();
            that.DataXHR = null;
        };
        if (!Configs.Data.polling) {
            this.StopPolling();
            return;
        };
        //轮询时检测是否登录超时
        if (!this.CheckLogin()) {
            return false;
        }
        if (!Configs.Data.complete) {
            if (args) {
                Configs.Data.interval = args['interval'] || 2500;
            }
        } else {
			if(Configs.Data.interval==Configs.Data.intervalUp){
				Configs.Data.interval = Configs.Data.intervalCache;
			}
        }
        this.polling = setTimeout(function () {
            that.isPolling = true;
            that.GetData();
            that.polling = null;
        }, Configs.Data.interval);
    },
    //停止轮询数据
    StopPolling: function () {
        if (this.polling) {
            clearTimeout(this.polling);
            this.polling = null;
        }
        if (this.DataXHR || this.DataXHR != null) {
            this.DataXHR.abort();
            this.DataXHR = null;
        }
    },
    /*---------------------------------*
    * 获取"数据"(JSON字符串)
    *---------------------------------*/
    GetData: function (argsInfo) {
        if (!Configs.Data.render) { this.StartPolling(); return; }
        var that = this;
        var args = argsInfo ? argsInfo : Configs.Template.info;
        if (this.DataXHR || this.DataXHR != null) {
            this.DataXHR.abort();
            this.DataXHR = null;
        };
		//判断是否需要轮询,并可设置轮询时间
		Configs.Data.polling = args.polling===false ? false : true;
		if(Configs.Data.polling){
			if(args.polling && $.type(args.polling) == "number"){
				Configs.Data.intervalCache = args.polling;
				Configs.Data.interval = args.polling;
			} else {
				Configs.Data.intervalCache = Configs.Data.defaultInterval;
				Configs.Data.interval = Configs.Data.intervalCache;
			}
		}
		var urls = Configs.Template.info["data"].split(",");
		var getTimes = 0;
		var datas = {}; //临时储存数据
		var cache = ""; //临时储存数据字符串
		var cacheData = "";
		get();
		function get(url){
			url = url ? url: urls[0];
			var key = null;
			//判断url是否有":"分隔
			if(/:/g.test(url)){
				var urlarr = url.split(":");
				url = urlarr[1];
				key = urlarr[0];
			}
			that.DataXHR = $.ajax({
				dataType: "html",
				//type: //args['method'] ? args['method'] : "GET",
				headers: {
					"If-None-Match": that.isPolling ? that.dataEtag : ""
				},
				url: url + "?_=" + new Date().getTime(),
				//url: Configs.Data.url + "?_=" + new Date().getTime(),
				data: args['parameter'] ? args['parameter'] : "",
				timeout: Configs.Data.timeout,
				beforeSend: function () {
					if (that.isPolling) {
						that.StopPolling();
					}
					if (that.SyncTimer) {
						clearTimeout(that.SyncTimer);
					}
					if (Configs.Template.info.sync) {
						var CurrentModule = $(document.getElementById(args["modules"]));
						var LoadingOrTip = CurrentModule.find("div.PromptLoading2").length != 0 || CurrentModule.find("div.PromptTip").length != 0;
						if (LoadingOrTip) {
							that.SyncTimer = setTimeout(function () {
								that.StartPolling();
							}, 5000);
						};
					}
				},
				//返回成功处理
				success: function (data, textStatus, jqXHR) {
					if (jqXHR.status == 200) {
						that.dataEtag = jqXHR.getResponseHeader("Etag");
						//判断是否请求cgi文件,是的话就不必判断文件是否完整,即sync为true则同步返回数据
						if (!Configs.Template.info.sync) {
							//判断数据是否完整
							var re = new RegExp(Configs.Data.endStr, 'g');
							if (re.test(data)) {
								Configs.Data.complete = true;
								data = data.replace(Configs.Data.endStr, "");
							} else {
								//数据不完整时轮询数据,且储存cache
								Configs.Data.cache = data;
								if (!that.isPolling) {
									Configs.Data.complete = false;
									//第一次加载页面时，才提示，轮询时不提示错误
									that.PromptEvent.Tip({ target: args["modules"], text: Language.Html['005'] + Configs.Prompt.refresh });
								}
								that.StartPolling({
									"interval": Configs.Data.intervalUp
								});
								return;
							}
						}
						cacheData +=data;
						//返回成功,判断数据是否有变化,打开新页面不比较,直接渲染,轮询的时候才比较
						//同步(即sync为true)返回数据时，只有数据返回出错才会轮询，这时候不需要比较
						if (that.isPolling && !Configs.Template.info.sync && (getTimes==urls.length-1)) {
							//比较相同则不渲染页面
							if (Configs.Data.cache == cacheData) {
								that.StartPolling();
								return;
							};
						};
						//获取数据成功时，储存数据缓存
						cache +=data;
						if(getTimes==urls.length-1){
							Configs.Data.cache = cache;
						}
						//判断JSON数据格式是否能正确解析
						try {
							data = jQuery.evalJSON(data);
							if(key!=null){
								var idata = {};
								idata[key] = data;
								data = idata;
							}
							datas = $.extend(true, {}, datas, data);
							if(getTimes==urls.length-1){
								data = datas;
							} else {
								//数据未取完前，依次取回数据
								getTimes++
								get(urls[getTimes]);
								return;
							}
						} catch (e) {
							//解析出错轮询数据
							if (!that.isPolling) {
								//第一次加载页面时，才提示，轮询时不提示错误
								that.PromptEvent.Tip({ target: args["modules"], text: Language.Html['001'] });
							}
							that.StartPolling();
							return;
						}
					} else if (jqXHR.status == 304) {
						//如果返回304,则继续轮询
						if (Configs.Data.complete) {
							that.StartPolling();
						} else {
							that.StartPolling({
								"interval": Configs.Data.intervalUp
							});
						}
						return;
					}
					//在数据存储之前，与前一次存的数据进行比较，判断哪个模块发生了变化
					if (Configs.HomePage) {
						if (that.isPolling) {
							//如果是首页,且在轮询状态时，判断哪个模块发生了变化，则更新哪个模块
							Configs.Modules.Renders = [];
							for (var Item in data) {
								if (jQuery.toJSON(data[Item]) != jQuery.toJSON(Configs.Data.content[Item] || "")) {
									Configs.Modules.Renders.push(Item);
								}
							}
						} else {
							//非轮询时,首页更新所有模块
							Configs.Modules.Renders = Configs.Modules.Defaults;
						}
					}
					//组织数据
					if (Configs.HomePage) {
						//浅拷贝,这里不能使用$.extend(true,Configs.Data.content,data)深拷贝,否则有些列表数据不能及时更新
						Configs.Data.content = data;

					} else {
						var newData = {};
						for (var n = 0, nlen = Configs.Modules.Renders.length; n < nlen; n++) {
							var rm = Configs.Modules.Renders[n];
							/*当有name值，且rm为mainBody时，将数据存储到mainContent里*/
							/*RenderData读取数据时，与这个保持一致的*/
							if (args["name"] && args["name"] != "") {
								if (rm == "mainBody") {
									rm = "mainContent";
								}
							}
							newData[rm] = data;
							if (data[rm]) {
								//判断请求的数据中是否有别的modules的数据，有的话则浅拷贝进去
								//$.extend(newData[rm], data[rm]);
								newData[rm] = data[rm]
							}
						}
						//$.extend(Configs.Data.content, newData);
						Configs.Data.content = newData;
					};
					//请求失败次数归0
					Configs.Data.failNum = 0;
					//渲染数据
					if (that.SyncTimer) {
						clearTimeout(that.SyncTimer);
					}
					/*用于advanced setting,如果返回98则登录超时*/
					if (data.status == 98) {
						that.PromptEvent.Tip({ target: args["modules"], text: Language.Html['019'] });
						that.StopPolling();
						return;
					};
					that.RenderData();
				},
				error: function (jqXHR, textStatus, errorThrown) {
					//如果中途某次加载失败,下次加载时，则需重新渲染页面
					that.dataEtag = "";
					Configs.Data.cache = "";
					if (textStatus != "abort") {
						that.DealError(textStatus, args, Configs.Data);
					}
				}
			}).always(function (jqXHR, textStatus, errorThrown) {
				jqXHR = null;
				textStatus = null;
				errorThrown = null;
				that.DataXHR = null;
			});
		};
    },
    DealError: function (textStatus, args, data) {
        var that = this;
        var args = args ? args : Configs.Template.info;
        var alarm = data == Configs.Alarm ? true : false;
        function Repolling() {
            if (alarm) {
                that.StartPollingAlarm();
            } else {
                that.StartPolling();
            }
        }
        //如果$("#wrapper")隐藏,表示是重载状态，不提示错误
        if (Configs.wrapper.is(":hidden")) {
            Repolling();
            return false;
        };
        function ShowTip(target, text) {
            var TipInfo = { target: target ? target : args["modules"], text: text ? text : Language.Html['036'] };
            if (alarm) {
                TipInfo.Class = "alarm-prompt";
            }
            that.PromptEvent.Tip(TipInfo);
        }
        if (alarm) {
            if (Configs.Data.polling && Configs.Data.fail == false) {
                data.failNum++;
                if (data.failNum >= data.failMax) {
                    if (document.getElementById("PromptLoading_alarm")) {
                        ShowTip("alarm", Language.Html["002"]);
                    } else if ($("#SetProgress")[0]) {
                        Pages.SetProcessDone(Language.Html["002"]);
                    }
                    data.failNum = 0;
                    data.cache = ""
                    that.alarmEtag = "";
                }
                that.StartPollingAlarm();
                return false;
            }
            args["modules"] = "alarm";
        }
        data.failNum++;
        //如果getFailMax次返回失败时，则提示错误,并clearInterval
        if (data.failNum >= data.failMax) {
            that.dataEtag = "";
            if (alarm) { that.alarmEtag = ""; }
            data.cache = "";
            data.failNum = 0;
            data.fail = true;
            var PromptLoading = $("div.PromptLoading2");
            function showError(text) {
                that.StopKeepLogin();
                that.StopPollingTrend();
                that.StopPolling();
                if (alarm) {
                    that.StopPollingAlarm();
                    if (Configs.Data.fail) {
                        ShowTip();
                        return false;
                    }
                } else {
                    if (Configs.Data.fail) {
                        that.StopPollingAlarm();
                    }
                }
                if (confirm(Language.Html["036"] + "\n\n" + Language.Html["036_1"])) {
                    Control.LoginOut();
                } else {
                    if (/IE/g.test(Configs.Browser)) {
                        window.opener = null;
                        window.open('', '_self');
                        window.close();
                        return
                    };
                    if (PromptLoading.length > 0) {
                        ShowTip();
                    } else if ($("#SetProgress")[0]) {
                        Pages.SetProcessDone(Language.Html["036"]);
                    }
                    jQuery.cookie("restart", "1", { path: "/" });
                    return false;
                }
                return false;
            }
            switch (textStatus) {
                case "parsererror":
                case "success":
                    showError(Language.Html['001']);
                    break;
                case "error":
                default:
                    showError(Language.Html['002']);
                    break;
            }
        } else {
            if (Configs.Template.info.sync && args["modules"] != "alarm") {
                clearTimeout(that.SyncTimer);
                Configs.Data.polling = false;
                that.PromptEvent.Tip({ target: args["modules"], text: Language.Html['002'] });
            }
            Repolling();
        }
    },
    /*---------------------------------*
    * 渲染"数据",把GetTemplate获取的模板与GetData获取的数据生成带数据的HTML代码，并写入到相应的Module里
    *---------------------------------*/
    RenderData: function () {
        if (!Configs.Data.render) { return; }
        var that = this;
        //复制info信息
        var args = $.extend(true, {}, args, Configs.Template.info);
		//如果fn不存在，可请求与template同名的js/文件，如tmp.setting_charge.html，就请求setting_charge.js
		//如果fn存在，则以数组的形式请求两个或多个文件,如页面tmp.setting_charge.html 的fn为"setting",将传递["settign","setting_charge"]
		//请求setting_charge.js和setting.js
		//如果fn设置为[false,"setting"]，即第一个参数为false,则不请求template同名js,false传递参数前会被删除,最终传递["setting"]
		var requireArrs = [];
		var requireArrsOne = "";
		if ($.type(args["fn"]) != "undefined" && $.trim(args["fn"]) != "") {
			//如果fn设置了回调js，那这个js必须要存在，否则会出错
			if (args["fn"] === false) {
				requireArrsOne = args["fn"];
			} else {
				requireArrs = (args["fn"] instanceof Array) ? args["fn"] : args["fn"].split(",");
				requireArrsOne = requireArrs[0];
			}
		}
		if (args["template"] && $.trim(args["template"]) != "") {
			//将模板同名数组添加进数组
			//fn可以设置数组第一个数为false,为false时将不加载同名template js文件
			//替换掉"tmp."、".html、".htm"
			var str_template = args["template"].replace(/tmp\.|\.html|\.htm/g, "");
			//判断args["template"]是否有加载公用模板,如果args["template"]用","号隔开有多个，则表示有公用模板加载
			//通常args["template"]最后一个为主模板，前面的为公用模板
			var argstemplates = /,/g.test(str_template) ? str_template.split(",") : str_template;
			var getMainJs = function (one) {
				if (one === false || one === "false") {
					requireArrs.shift();
				} else {
					if (one === true || one === "true") {
						requireArrs.shift();
					}
					var newCallback = argstemplates instanceof Array ? argstemplates[argstemplates.length - 1] : argstemplates;
					if (jQuery.inArray(newCallback, requireArrs) == -1) {
						requireArrs.push(newCallback);
					}
				}
			};
			if (requireArrsOne instanceof Array) {
				if (argstemplates instanceof Array) {
					var atLen = argstemplates.length;
					var raoLen = requireArrsOne.length;
					//先循环加载所需要的js
					for (var g = 0; g < raoLen; g++) {
						if (argstemplates[g] && requireArrsOne[g] == true) {
							requireArrs.push(argstemplates[g])
						}
					}
					//如果requireArrsOne的长度小于argstemplates的长度，则默认追加主模板js
					if (raoLen < atLen) {
						requireArrs.push(argstemplates[atLen - 1])
					}
				} else {
					//如果template只有一个，却用数组形式[]设置fn，则取fn[0]
					getMainJs(requireArrsOne[0]);
				}
				requireArrs.shift();
			} else {
				getMainJs(requireArrsOne);
			};
		};
		args["fn"] = requireArrs;
		var errTimer = null;
		require(requireArrs, function () {
			dorender();
		}, function (err) {
			clearTimeout(errTimer);
			errTimer = setTimeout(function () { dorender(); }, 50);
		});
        
        function dorender() {
            //读取模板、数据
            if (Control.isPolling && Configs.HomePage) {
                var modules = ["mainContent", "sider"];
            } else {
                var modules = Configs.Modules.Renders;
            }
            var templates = Configs.Template.content;
            var datas = Configs.Data.content;
	    //默认设置从"mainContent"取数据，若取不到函数GetDatasFromName()会判断从modules对应的地方取，再取不到会设置为空对象{}
            var datas_maincontent = datas["mainContent"];
            var modulesLength = modules.length;
            //如果modulesLength==0，return; ==1不循环，>1时才循环,提高性能;
            var name = args["name"];
            var doRender = args["render"];
            var htmlDatas = "";
            if (modulesLength <= 0) {
                return false;
            } else if (modulesLength == 1) {
                var iModuleName = modules[0];
                var iModule = document.getElementById(iModuleName);
                var templatehtml = templates[iModuleName];
				if(!templatehtml) { return; }
                //这句不要更新到共享，只是为了本地显示没有替换的数据
                //templatehtml = templatehtml.replace(/\/\*\[ID_/g, "").replace(/\]\*\//g, "");
                var data = {
                    "args": args,
                    "data": {}
                };
                data["data"] = GetDatasFromName(name, data["data"]);
                if (data.data && iModule && templatehtml != "") {
                    that.PromptEvent.Loading({ remove: iModuleName });
                    Pages.Int = null;
                    if (doRender == "artTemplate") {
                        data["jQuery"] = data["$"] = jQuery;
                        data["Configs"] = Configs;
                        data["Pages"] = Pages;
                        data["Control"] = Control;
                        data["Validates"] = Validates;
                        data["window"] = window;
                        try {
                            var render = template.compile(templatehtml);
                            htmlDatas = render(data);
                            HTMLModule(iModule, htmlDatas, iModuleName, data, true);
                        } catch (err) {
                            CatchError(iModuleName,err);
                        }
                    } else {
                        try {
                            htmlDatas = doT.template(templatehtml)(data);
                            HTMLModule(iModule, htmlDatas, iModuleName, data, true);
                        } catch (err) {
                            CatchError(iModuleName,err);
                        }
                    }

                };
            } else {
                //循环输出modules的数据;
                for (var i = 0, ilen = modules.length; i < ilen; i++) {
                    //当前模块
                    var iModuleName = modules[i];
                    var iModule = document.getElementById(iModuleName);
                    //当前数据名
                    var name = args["name"];
                    //定义单模块数据
                    var data = {
                        "args": args,
                        "data": {}
                    };
                    //定义单模块模板
                    var templatehtml = templates[iModuleName];
		   if(!templatehtml) { continue; }
                    //这句不要更新到共享，只是为了本地显示没有替换的数据
                    //templatehtml = templatehtml.replace(/\/\*\[ID_/g, "").replace(/\]\*\//g, "");
                    data["data"] = GetDatasFromName(name, data["data"]);
                    //如果数据中存在二级tab,则把它带入到页面数据中	
                    if (datas_maincontent && datas_maincontent['subMenu']) {
                        data['data']['subMenu'] = datas_maincontent['subMenu'];
                    }
                    if (data.data && iModule && templatehtml != "") {
                        //清除当前模块数据的提示
                        that.PromptEvent.Loading({ remove: iModuleName });
                        //写入数据前，初始化Pages.Int函数为null;
                        Pages.Int = null;
                        //写入模块数据
                        if (doRender == "artTemplate") {
                            data["jQuery"] = data["$"] = jQuery;
                            data["Configs"] = Configs;
                            data["Pages"] = Pages;
                            data["Control"] = Control;
                            data["Validates"] = Validates;
                            data["window"] = window;
                            try {
                                var render = template.compile(templatehtml);
                                htmlDatas = render(data);
                                HTMLModule(iModule, htmlDatas, iModuleName, data, i == ilen - 1);
                            } catch (err) {
                                CatchError(iModuleName,err);
                            };
                        } else {
                            try {
                                htmlDatas = doT.template(templatehtml)(data);
                                HTMLModule(iModule, htmlDatas, iModuleName, data, i == ilen - 1);
                            } catch (err) {
                                CatchError(iModuleName,err);
                            };
                        }
                    }
                };
            };
            function HTMLModule(target, htmls, iModuleName, idata, last) {
                $(target).children().off();
                if (target) {
                    $(target).html(htmls);
                }
				switch (iModuleName){
					case "header":
					case "sider":
					case "mainBar":
					case "footer":
						if ($.type(Pages[iModuleName]) == "function") {
							Pages[iModuleName](idata);
						}
						break;
					default:
						//运行modules对应的函数做为回调
						if ($.type(Pages[iModuleName]) == "function") {
							Pages[iModuleName](idata);
						}
						//运行与template同名的函数做为回调
						Pages.CallBack(idata);
				}
                //重新设计布局,如果是Alarm展开查看状态，不自动布局
                if (!Configs.Alarm.expand && (iModuleName == "mainBody" || iModuleName == "mainContent")) {
                    that.SetLayout();
                };
                if (last) {
                    that.StartPolling();
                }
            };
            function CatchError(iModuleName,err) {
                if (!that.isPolling) {
                    var target = "";
                    if (iModuleName == "mainBody") {
                        target = $("#mainBody");
                    } else {
                        target = $("#mainContent");
                    };
                    setTimeout(function () {
                        that.PromptEvent.Tip({ target: target, text: Language.Html["047"]+"<span class='error-tip'>"+(err.message || err)+"</span>", clear: true });
                    }, 100);
                };
            };
            function GetDatasFromName(name, data) {
                //判断是否有name值,有则在mainContent对象里的name数据,否则取对应模块的数据
                if (name && name != "") {
                    //依","split name值,如果split后的数组长度大于1，则循环加载加个数据进data["data"];
                    //主要是用于获取某些公共数据
                    var nameArr = name.split(","), nameArrLength = nameArr.length;
			//如果mainContent没有数据，则去modules里取，再没有则设置为{} 
			if (!datas_maincontent) {
				datas_maincontent = datas[iModuleName];
			}
			if(datas_maincontent){
				if (nameArrLength > 1) {
					for (var j = 0; j < nameArrLength; j++) {
						data[nameArr[j]] = datas_maincontent[nameArr[j]] || {};
					}
				} else {
					data = datas_maincontent[name] || {};
				};
			} else {
                        	data = {};
                    	}
                } else {
                    if (args['idata'] && args['idata'] != "" && datas[args['idata']]) {
                        data = datas[args['idata']];
                    } else if (datas[iModuleName]) {
                        data = datas[iModuleName];
                    } else {
                        data = {}
                    }
                };
                if (datas_maincontent) {
                    if (datas_maincontent["COMMON"]) {
                        data["COMMON"] = datas_maincontent["COMMON"];
                    }
                }
                return data;
            };
			//定位当前栏目
			that.SetNavigation();
		};
    },
    /*---------------------------------*
    * 设置布局,窗口变动或alarm变化时，重置布局
    *---------------------------------*/
    ResetLayout: true,
    SetLayout: function (a) {
        //0->H_header,1->H_footer,2->H_mainBar,3->H_mainTab,4->H_alarmMax,5->H_alarmMin;
        var doc = document;
        var H = [126, 35, 0, 40, 198, 28],//[92, 32, 37, 37, 198, 28]
            H_window = $(window).height(),
            H_body = $(doc).height(),
            container = $(doc.getElementById("container")),
            content = $(doc.getElementById("content")),
            mainTab = $(doc.getElementById("mainTab")),
            mainBody = $(doc.getElementById("mainBody")),
            alarm = $(doc.getElementById("alarm")),
            alarmList = $(doc.getElementById("alarmList")),
            alarmContent = $(doc.getElementById("alarmContent")),
            alarmHandle = $("a.alarmHandle");
       //if (Configs.HomePage) {
            alarm.css({ "z-index": "99999" });
       // } else {
       //     alarm.css({ "z-index": "999" });
       // }
        if (a) {
            //a为true时,指点system alarm的提示弹开
            var h = container.height();
            alarm.css({
                "height": h - 38,
                "right":"270px"
            });
            alarmList.css("height", h - 60 - 37);
            alarmContent.show();
            alarmHandle.removeClass("alarmOpen").addClass("alarmClose");
        } else {
            //设置alarm高度
            if (Configs.Alarm.show) {
                alarmHandle.removeClass("alarmOpen").addClass("alarmClose")
                alarm.css({ "height": H[4],"right":"270px" });
                alarmContent.show();
            } else {
                alarmHandle.removeClass("alarmClose").addClass("alarmOpen")
                alarm.css({ "height": H[5],"right":"270px" });
                alarmList.css({ "height": 141 })
                alarmContent.hide();
				var alarmTip = $(doc.getElementById("PromptTip_alarm"));
				var alarmLoading = $(doc.getElementById("PromptLoading_alarm"));
				alarmTip.add(alarmLoading).css({"top":0})
            }
			var sider = $(doc.getElementById("sider"));
			var sideHeight = sider.find("ul.sider-list").outerHeight(true)+H[0]+H[1]-1;//+sider.find("div.sider-info").outerHeight(true)
            //sideHeight为左侧导航的最低高度
            var H_content = (H_window < sideHeight ? sideHeight : H_window) - H[0]-H[1];
            container.css("height", H_content-H[2]);
            content.css("height", H_content);
            //设置mainBody高度
            var H_mainBodyNew = H_content - H[2] - (mainTab[0] ? H[3] : 0)  - H[5] - 10 - (/IE/gi.test(Configs.Browser) ? 2 : 1);
            mainBody.css("height", H_mainBodyNew+39).scrollTop(Configs.MainScrollHeight);
        }
        var t2 = document.getElementById("history_t2");
        if (t2) {
            var HistorySummary = mainBody.find("#history_summary");
            var t1 = mainBody.find("#history_t1");
            $(t2).height(mainBody.height() - HistorySummary.outerHeight(true) - t1.outerHeight(true) - 48);
        }
        $(".extbackground").css({"min-height":H_window-H[0]-H[1]-H[3],"height":mainBody.height()});
        $("#Setting_TL1_Signal .table-container,.set-form-TL1-signal").css({"height":$("#mainBody").height()-($(".TL1-signal-summary").outerHeight()+5)});
        $("#Setting_TL1_Signal .table-body").css({"height":$("#mainBody").height()-($(".TL1-signal-summary").outerHeight()+5)-($("#Setting_TL1_Signal .table-container .table-title").height()+21)});
        //如果设置网页高度失败，则重新设置
        if (this.ResetLayout) {
            //mainBody默认高度为300
            if ($("#mainBody").height() == 300) {
                var that = this;
                setTimeout(function () {
                    that.SetLayout();
                }, 100);
            } else {
                this.ResetLayout = false;
            }
        }
    },
    SetNavigation: function (args) {
		args = args ? args : Configs.Template.info;
    //disabledNav为true时，不更新导航
		if(args.disabledNav){ return; }
        if ($.type(args["currentMenu"]) != "array") {
			//currentMenu不是数组时，表示确切的某个<a>，只要在这个<a>上添加currentMenu;
			var tabCurrent = /#/g.test(args["currentMenu"]) ? $(args["currentMenu"]) : $("#"+args["currentMenu"]);
			if(!tabCurrent[0]){ return false; }
			tabCurrent = tabCurrent[0] ? tabCurrent : null;
			if (tabCurrent != null) {
				tabCurrent.addClass("currentMenu");
			}
		}
		//currentMenu未设置或是数组时，第一项表示要定位的范围列表，第二项表示从0开始的第几个添加currentMenu样式
        var currentList = $(args["currentMenu"][0]);
		//if(currentList.length==0 || !currentList.get(args["currentMenu"][1])){ return false; }
		var navigation = Configs.Navigation;
        var menuIndex = Number(args["menuIndex"]);
        var currentMenu = "currentMenu";
        var text = args["text"];
        var mainBar = $("#mainBar");
        var mainTab = $("#mainTabContent")[0] ? $("#mainTabContent") : $("#mainTab");
        //当menuIndex为1时，navigation.nav的长度为1，以下类推
        if (menuIndex == 0) {
            //0为特殊值,表示隶属于home的单独页面
            navigation.nav.length = 1;
            navigation.nav[0] = "<i>" + text + "</i>";
            currentList.removeClass(currentMenu).eq(args["currentMenu"][1]).addClass(currentMenu);
        } else if (menuIndex == 1) {
            var text2 = $.trim(mainTab.find("a:first").text());
            if (args["currentMenu"][1] == 0) {
                navigation.nav.length = 1;
                navigation.nav[0] = "<i>" + text2 + "</i>";
            } else {
                if (text2 == "") {
                    navigation.nav.length = 1;
                } else {
                    navigation.nav.length = 2;
                    navigation.nav[1] = "<i>" + text2 + "</i>";
                };
                navigation.nav[0] = "<i>" + text + "</i>";
            };
            currentList.removeClass(currentMenu).eq(args["currentMenu"][1]).addClass(currentMenu);
        } else if (menuIndex == 2) {
            navigation.nav.length = 2;
            navigation.nav[1] = "<i>" + text + "</i>";
            var current = currentList.eq(args["currentMenu"][1]);
            if (current[0]) {
                currentList.removeClass(currentMenu);
                current.addClass(currentMenu);
            } else {
                //单独页面，如system->rectifier，是哪页就显示哪页
            }
        };
        if (navigation['nav'][0] == navigation['nav'][1]) {
            navigation['nav'].pop();
        }
        var mainBarData = {
            "nav": navigation['nav'].join(Configs.Navigation.space),
            "navsp": Configs.Navigation.space
        };
        var htmlDatas = "";
        try {
            var doTtmpl = doT.template(Configs.Template.content['mainBar']);
            htmlDatas = doTtmpl(mainBarData);
        } catch (err) { }
        if (mainBar[0]) {
            mainBar[0].innerHTML = htmlDatas;
        }
        //Pages.mainBar(args);
    },
    //轮询数据
    StartPollingAlarm: function () {
        var that = this;
        if (this.AlarmXHR || this.AlarmXHR != null) {
            this.AlarmXHR.abort();
            this.AlarmXHR = null;
        };
        this.pollingAlarm = setTimeout(function () {
            that.isAlarmPolling = true;
            that.GetAlarms();
            that.pollingAlarm = null;
        }, Configs.Alarm.interval);
    },
    //停止轮询数据
    StopPollingAlarm: function () {
        if (this.pollingAlarm) {
            clearTimeout(this.pollingAlarm);
            this.pollingAlarm = null;
        }
        if (this.AlarmXHR || this.AlarmXHR != null) {
            this.AlarmXHR.abort();
            this.AlarmXHR = null;
        }
    },
    GetAlarms: function () {
        var that = this;
        if (Configs.Alarm.requestCount >= Configs.Alarm.refresh) {
            Configs.Alarm.requestCount = 0;
            //重置下面字段，强制alarm刷新模块
            //设置新字段为所有数字字母，确保与返回的值不可能相等
            that.alarmEtag = "0123456789abcdefghijklmnopqrstuvwxyz";
            Configs.Alarm.cache = "0123456789abcdefghijklmnopqrstuvwxyz";
            that.isAlarmPolling = false;
        };
        Configs.Alarm.requestCount++;
        that.AlarmXHR = $.ajax({
            timeout: Configs.Alarm.timeout,
            dataType: "html",
            headers: {
                "If-None-Match": that.isAlarmPolling ? that.alarmEtag : ""
            },
            url: Configs.Alarm.url + "?_=" + new Date().getTime(),
            beforeSend: function () {
                if (!that.isAlarmPolling) {
                    that.PromptEvent.Loading({ target: "alarm", interval: 200, clear: false });
                }
            },
            success: function (data, textStatus, jqXHR) {
                if (jqXHR.status == 200) {
                    that.alarmEtag = jqXHR.getResponseHeader("Etag");
                    //判断数据是否完整
                    var re = new RegExp(Configs.Data.endStr, 'g');
                    if (re.test(data)) {
                        data = data.replace(Configs.Data.endStr, "");
                    } else {
                        //数据不完整时轮询数据,并储存cache
                        Configs.Alarm.cache = data;
                        if (!that.isAlarmPolling) {
                            //第一次加载页面时才提示，轮询时不提示错误
                            setTimeout(function () {
                                that.PromptEvent.Tip({ target: "alarm", text: Language.Html["005"],Class:"alarm-prompt"});
                            }, 200)
                        }
                        that.StartPollingAlarm();
                        return;
                    }
                    //返回成功,判断数据是否有变化
                    if (Configs.Alarm.cache == data) {
                        if (that.isAlarmPolling) {
                            that.StartPollingAlarm();
                            return;
                        }
                    };
                    //缓存上一次的数据
                    Configs.Alarm.cache = data;
                    //判断JSON数据格式是否能正确解析
                    try {
                        data = jQuery.evalJSON(data);
                    } catch (e) {
                        //解析出错轮询数据
                        if (!that.isAlarmPolling) {
                            //第一次加载页面时，才提示，轮询时不提示错误
                            setTimeout(function () {
                                that.PromptEvent.Tip({ target: "alarm", text: Language.Html['001'],Class:"alarm-prompt"});
                            }, 200)
                        }
                        that.StartPollingAlarm();
                        return;
                    }
                } else if (jqXHR.status == 304) {
                    //如果返回304,则继续轮询
                    that.StartPollingAlarm();
                    return;
                }
                Configs.Alarm.data = data;
                Pages.SetCommons();
                if (!Configs.Template.content['alarm']) {
                    Configs.Template.content['alarm'] = $("#tmp_alarm").html();
                }
                that.PromptEvent.Loading({ remove: "alarm" });
                if (Configs.Template.content['alarm'] && data) {
                    var alarm = $("#alarm");
                    try {
                        var doTtmpl = doT.template(Configs.Template.content['alarm']);//.replace(/\/\*\[ID_/g, "").replace(/\]\*\//g, ""));
                        if (alarm[0]) {
                            alarm.html(doTtmpl(data));
                        };
                    } catch (err) {
                        if (!that.isAlarmPolling) {
                            setTimeout(function () {
                                that.PromptEvent.Tip({ target: alarm, text: Language.Html["047"], clear: true,Class:"alarm-prompt"});
                            }, 100);
                        };
                    };
                    Pages.alarm(data);
                }
                that.isAlarmPolling = true;
                that.StartPollingAlarm();
		that.PromptEvent.TipRemove({"remove":"alarm"});
            },
            error: function (data, textStatus) {
                //如果中途某次加载失败,下次加载时，则需重新渲染页面
                that.alarmEtag = "";
                Configs.Alarm.cache = "";
                if (textStatus != "abort") {
                    that.DealError(textStatus, null, Configs.Alarm);
                }
            }
        }).always(function (jqXHR, textStatus, errorThrown) {
            jqXHR = null;
            textStatus = null;
            errorThrown = null;
            that.AlarmXHR = null;
        })
    },
    SetAlarmPopup: function () {
        //把alarm是否自动弹出的状态写入cookie
        jQuery.cookie("alarmAutoPop", jQuery.cookie("alarmAutoPop") || Configs.Alarm.auto, { path: "/" });
    },
    //轮询数据
    StartPollingTrend: function (interval) {
        if (this.TrendXHR || this.TrendXHR != null) {
            this.TrendXHR.abort();
        };
        if (interval) {
            var time = interval;
        } else {
            var time = Configs.Trend.interval;
        }
        var that = this;
        this.pollingTrend = setTimeout(function () {
            clearTimeout(that.pollingTrend);
            that.GetTrend();
        }, time);
    },
    //停止轮询数据
    StopPollingTrend: function () {
        if (this.pollingTrend) {
            clearTimeout(this.pollingTrend);
        }
        if (this.TrendXHR || this.TrendXHR != null) {
            this.TrendXHR.abort();
            this.TrendXHR = null;
        }
    },
    /*---------------------------------*
    * 获取Trend数据
    *---------------------------------*/
    GetTrend: function (refresh) {
        var that = this;
        if (refresh) {
            that.trendEtag = new Date().getTime();
        }
        this.TrendXHR = $.ajax({
            timeout: Configs.Data.timeout,
            dataType: "html",
            headers: {
                "If-None-Match": that.isTrendPolling ? that.trendEtag : ""
            },
            beforeSend: function () {
                if (!that.isTrendPolling) {
                    that.PromptEvent.Loading({ target: "Trend", interval: 200, marginTop: "center", clear: false });
                }
            },
            url: Configs.Trend.url + "?_=" + new Date().getTime(),
            success: function (data, textStatus, jqXHR) {
                if (jqXHR.status == 200) {
                    that.trendEtag = jqXHR.getResponseHeader("Etag");
                    //如果getFailMax(默认为6次)次返回失败，则提示错误,并clearInterval
                    if (Configs.Trend.failNum >= Configs.Trend.failMax) {
                        trendReload();
                        return;
                    };
                    //判断数据是否完整
                    var re = new RegExp(Configs.Data.endStr, 'g');
                    if (re.test(data)) {
                        data = data.replace(Configs.Data.endStr, "");
                    } else {
                        //数据不完整时轮询数据
                        //数据不完整时，还是要储存cache
                        Configs.Trend.dataCache = data;
                        Configs.Trend.failNum++;
                        Configs.Trend.fail_200 = true;
                        that.StartPollingTrend(Configs.Trend.tempInterval);
                        return;
                    }
                    //返回成功,判断数据是否有变化
                    if (Configs.Trend.dataCache == data) {
                        that.StartPollingTrend(Configs.Trend.tempInterval);
                        return;
                    };
                    //获取数据成功时，储存数据缓存
                    Configs.Trend.dataCache = data;
                    //判断JSON数据格式是否能正确解析
                    try {
                        data = jQuery.evalJSON(data);
                        Configs.Trend.failNum = 0;
                        Configs.Trend.fail_200 = false;
                    } catch (e) {
                        Configs.Trend.failNum++;
                        Configs.Trend.fail_200 = true;
                        if (!$("#Trend_canvas")[0]) {
                            that.PromptEvent.Tip({ target: "Trend", text: Language.Html['001'], marginTop: "center" });
                        }
                        //解析出错轮询数据
                        that.StartPollingTrend(Configs.Trend.tempInterval);
                        return;
                    }
                } else if (jqXHR.status == 304) {
                    if (Configs.Trend.fail_200) {
                        Configs.Trend.failNum++;
                        //如果getFailMax(默认为6次)次返回失败，则提示错误,并clearInterval
                        if (Configs.Trend.failNum >= Configs.Trend.failMax) {
                            trendReload();
                            return;
                        };
                    };
                    if (Configs.Trend.data.value) {
                        that.StartPollingTrend();
                    } else {
                        that.StartPollingTrend(Configs.Trend.tempInterval);
                    }
                    return;
                };
                Configs.Trend.data_y = $.extend(true, {}, Configs.Trend.data_y, data);
                //data值都除以totalCurrent;
                if (data.totalCurrent != 0) {
                    for (var v = 0, vlen = data.value.length; v < vlen; v++) {
                        data.value[v][1] = (data.value[v][1] / data.totalCurrent) * 100; //这里转化成百分比
                    };
                };
                Configs.Trend.data = data;
                that.isTrendPolling = true;
                that.StartPollingTrend();
                Pages.HomeTrend();
            },
            error: function (data, textStatus) {
                if (Configs.Trend.fail_200 && Configs.Trend.failNum != 0) {
                    Configs.Trend.fail_200 = false;
                    Configs.Trend.failNum = 0;
                }
                Configs.Trend.failNum++;
                //如果getFailMax(默认为6次)次返回失败，则提示错误,并clearInterval
                if (Configs.Trend.failNum >= Configs.Trend.failMax) {
                    if (Configs.wrapper.is(":hidden")) {
                        Configs.Trend.fail_200 = false;
                        Configs.Trend.failNum = 0;
                        return false;
                    }
                    trendReload();
                    return;
                }
                that.StartPollingTrend(Configs.Trend.tempInterval);
            }
        }).always(function (jqXHR, textStatus, errorThrown) {
            jqXHR = null;
            textStatus = null;
            errorThrown = null;
            that.TrendXHR = null;
        });
        function trendReload(reloadNum) {
            //中断时 Trend不提示错误
            if (!that.isTrendPolling) {
                that.PromptEvent.Tip({ target: "Trend", text: Language.Html['002'] + Configs.Prompt.refresh_trend, marginTop: "center" });
            };
            if (!reloadNum) {
                //如果不归0，则只重新加载一次
                Configs.Trend.failNum = 0;
            } else {
                Configs.Trend.failNum = reloadNum;
            };
        }
    },
    /*---------------------------------*
    * 保持登录状态，每隔5少POST一次数据到服务器
    *---------------------------------*/
    KeepLoginPolling: null,
    StopKeepLogin: function () {
        clearTimeout(this.KeepLoginPolling);
        this.KeepLoginPolling = null;
    },
    KeepLogin: function () {
        var that = this;
        //每隔5秒post数据到CGI，维持连接
        function PostData() {
            var XHR = $.ajax({
                timeout: Configs.Alarm.timeout,
                url: "/app/www_user/html/cgi-bin/web_cgi_control.cgi?_=" + new Date().getTime(),
                data: "equip_ID=1&control_type=16&sessionId=" + jQuery.cookie("sessionId"),
                success: function (data, textStatus, jqXHR) {
                    try {
                        var datas = jQuery.evalJSON(data);
                        if (datas.status == 1) {
                            Pages.footer({
                                data: {
                                    present_time: datas.content[0] //data.content[0]时间为秒
                                }
                            });
                        }
                    } catch (Error) { }
                    datas = null;
                },
                error: function (data, textStatus) { }
            }).always(function (jqXHR, textStatus, errorThrown) {
                jqXHR = null;
                textStatus = null;
                errorThrown = null;
                XHR = null;
                that.KeepLoginPolling = setTimeout(function () {
                    PostData();
                }, 5000);
            });
        };
        PostData();
    },
    MouseMoveTimer: null,
    ReloadTimer: null,
    Reload: function () {
        var that = this;
        this.ReloadTimer = setTimeout(function () {
            clearTimeout(that.ReloadTimer);
            that.ReloadTimer = null;
            that.RemoveFrames(true);
            location.reload();
        }, 900000); //15分钟未操作则返回首页
    },
    StopReload: function () {
        clearTimeout(this.MouseMoveTimer);
        clearTimeout(this.ReloadTimer);
        Configs.StopReload = true;
    },
    RemoveFrames: function (reload) {
        //用在reload()前，移除iframe,避免iframe内存泄漏
        var frame = $("iframe");
        if (frame.length > 0) {
            for (var i = 0, ilen = frame.length; i < ilen; i++) {
                var f = frame.eq(i);
                if (f.attr("keep") != "") {
                    break;
                } else {
                    f[0].src = "about:blank";
                    f[0].contentWindow.document.write('');
                    f[0].contentWindow.close();
                    f[0].contents().children().off().remove();
                    f.remove();
                    f = null;
                }
            }
            if (/IE/g.test(Configs.Browser)) {
                CollectGarbage();
            }
        }
        if (reload) {
            //reload前移除所有DOM，防止reload时DOM泄漏
	    $("#contextmenu").remove();
            $("body").off();
            $(document).off();
            Configs.wrapper.html('');
        };
    },
    /*---------------------------------*
    * 初始化函数，页面加载完第一次就运行Initialization();
    *---------------------------------*/
    Initialization: function () {
        var that = this;
		//启用自定义alert函数
		/*
		window.alert = function(txt){ 
			return Control.PromptEvent.Alert(txt);
		}
		*/
        /*判断是否为重启状态，是的话返回登录页面*/
        this.CheckReLogin();
        //初始化时区
        Configs.timezone = new Date().getTimezoneOffset() / 60;
        //预存相关dom，避免每次都取
        Configs.wrapper = $(document.getElementById("wrapper"));
        //预存浏览器类型
        Configs.Browser = $.isBrowser();
        //初始化一些Html代码
        Configs.Prompt = {
            status: false,
            module: null,
            refresh: "<a href='#' onclick='Control.RefreshModule();return false;' class='PromptRefresh'>" + Language.Html['027'] + "</a>",
            refresh_trend: "<a href='#' onclick='Control.GetTrend(true);return false;' class='PromptRefresh'>" + Language.Html['027'] + "</a>",
            relogin: "<a href='#'class='btn_set' onclick='Control.LoginOut();return false;'><i>" + Language.Html['024'] + "</i></a>",
            retry: "<a href='#' class='btn_set resetSendSubmit' onclick='return false;'><i>" + Language.Html['017'] + "</i></a>",
            cancel: "<a href='#' class='btn_set close' onclick='return false;'><i>" + Language.Html['015'] + "</i></a>"
        };
        var keyupTimer = null;
        $(document).off().on("keydown", function (event) {
            var key = event.keyCode;
            if (key == 116) {
                //禁用F5刷新
                return false;
            } else if (key == 27) {
                if (/IE/g.test(Configs.Browser)) {
                    //使用IE时，禁用esc键
                    return false;
                }
            } else if (key == 8) {
                //非input focus时禁用Backspace;
                if (!Configs.Backspace) {
                    return false;
                }
            } else if(event.ctrlKey && key==82){
				//禁用ctrl+R刷新
				//return false;
			}
			
        }).on("contextmenu", function (e) {
            ///禁用右键,启用自定义右键
            var PromptCover = $("#PromptCover")[0];
            if (PromptCover) {
                return false;
            };
            var rdiv = document.getElementById("contextmenu");
            //1 = 鼠标左键; 2 = 鼠标中键; 3 = 鼠标右键
            //Configs.Template.info.data = Configs.Data.url;
            if (e.which === 3 || e.which === 0) {
                if (rdiv) {
                    rdiv.style.visibility = "visible";
                } else {
                    var rdiv = document.createElement("div");
                    rdiv.id = "contextmenu";
                    rdiv.className = "contextmenu";
                    rdiv.innerHTML = [
                        "<ul>", "<li><a href='#' onclick='Control.RefreshModule();return false;'>" + Language.Html["034"] + "</a></li>", "<li><a href='#' onclick='Control.RemoveFrames(true);location.reload();return false;'>" + Language.Html["035"] + "</a></li>", "</ul>"
                    ].join("");
                    $("body")[0].appendChild(rdiv);
                };
                var pLeft, pTop, winwidth = $(window).width(), winheight = $(window).height(), width = $(rdiv).outerWidth(true), height = $(rdiv).outerHeight(true);
                if (e.clientX + width > winwidth) {
                    //5->在最右边时，间隔5px
                    pLeft = winwidth - width - 5;
                } else {
                    if (e.clientX <= 0) {
                        //5->在最左边时，间隔5px
                        pLeft = 5;
                    } else {
                        pLeft = e.clientX;
                    }
                };
                if (e.clientY + height > winheight) {
                    pTop = winheight - height - 5;
                } else {
                    if (e.clientY <= 0) {
                        pTop = 5;
                    } else {
                        pTop = e.clientY;
                    };
                }
                var scrolltop = $(window).scrollTop() || 0;
                $(rdiv).css({ "left": pLeft, "top": pTop + scrolltop });
            }
            if ($("div.table-body ul.select")[0]) {
                $("ul.select").removeClass("select");
            }
            return false;
        }).on("click", function (e) {
            if (e.which !== 3) {
                var rdiv = document.getElementById("contextmenu");
                if (rdiv) {
                    rdiv.style.visibility = "hidden";
                }
                if (Pages.SystemPop) {
                    $("div.system-popup").hide();
                    Configs.Popup.index = null;
                    Configs.Popup.status = false;
                }
            }
            if (e.target.nodeName == "BODY") {
                if ($("div.table-body ul.select")[0]) {
                    $("ul.select").removeClass("select");
		    Configs.Data.setting = {};
		    Configs.HighLight = null;
                }
            }
        }).on("mousemove", function () {
            if (Configs.HomePage || Configs.StopReload) { return; }
            //移动鼠标时清除reload()动作
            clearTimeout(that.ReloadTimer);
            that.ReloadTimer = null;
            clearTimeout(that.MouseMoveTimer);
            //监测鼠标移动,如果鼠标15分钟未移动,则reload()一次页面
            that.MouseMoveTimer = setTimeout(function () {
                that.Reload();
                mousemove_timer = null;
            }, 5000);
        }).on("mouseup", function (e) {
            if (Configs.SelectFocus != null) {
                var t = $(e.target);
                var type = (t.attr("type") || t[0].nodeName).toLowerCase();
                if (type == "option") { t = t.parent(); }
                if (!t.is(Configs.SelectFocus)) {
                    Configs.SelectFocus.blur();
                }
            }
        });
        //加载reload()机制,主页15分钟reload()一次，其他页面鼠标停留15分钟不动后reload()一次
        that.Reload();
        //刚打开页面时检查是否登录
        if (!this.CheckLogin()) {
            return false;
        };
        this.SetAlarmPopup();
        //初始化时,缓存index页面的各模块的模板,便于后面的使用
        var modules = Configs.Modules.Defaults;
        for (var i = 0, ilen = modules.length; i < ilen; i++) {
            var template = document.getElementById(Configs.Template.prefix + modules[i]);
            if (template) {
                Configs.Template.content[modules[i]] = template.innerHTML;
            }
        };
        //窗口resize,resize里头添加了一个setTimeout，修正resize多次执行的问题
        var resize_timer = 0;
        $(window).resize(function () {
            clearTimeout(resize_timer);
            resize_timer = setTimeout(function () {
                that.SetLayout();
                var Cover = document.getElementById("PromptCover");
                if (Cover) {
                    that.PromptEvent.Cover({ target: Cover });
                }
                that.PromptEvent.Loading({ reset: true, marginTop: that.PromptEvent.ResetStatus });
				Control.RefreshModule(Configs.refresh);
            }, 200);
			//触发一次mainBody滚动事件
			//如历史如果页面，thead激动层在窗口变化时，需要重新定位
			var mainBody = document.getElementById("mainBody");
			if(mainBody){
				$(mainBody).trigger("scroll");
			}
        })
        $("body").on("click", function () {
            var contextmenu = document.getElementById("contextmenu");
            if (contextmenu) {
                $(contextmenu).css({ "visibility": "hidden" });
            }
        });
        //使用GetTemplate获取首页模板,继而获取数据
        var indexDatas = {
            "menuIndex": 1,
            "template": Configs.Template.info["template"],
            "modules": "mainContent",
            "currentMenu": ["ul.sider-list a", 0],
            "fn": [false, "HomePage"],
            "level": jQuery.cookie("nAuthority"),
            "sessionId": jQuery.cookie('sessionId'),
            "data": Configs.Template.info["data"]
        };
        that.GetTemplate(indexDatas);
        //控制浏览器历史记录
        $.history.init(indexDatas);
        //设置Configs.Cookies.names
        var cookie_items = document.cookie.split(";");
        for (var i = 0, ilen = cookie_items.length; i < ilen; i++) {
            var tmp_arr = cookie_items[i].split("=");
            Configs.Cookies.names.push($.trim(tmp_arr[0]));
        };
        //获取trend数据
        that.GetTrend();
        //轮询alarms
        that.GetAlarms();
        //保持登录连接
        that.KeepLogin();
        //测试js时间轴test_timer
        setTimeout(function () {
            Configs.test_timer = true;
        }, 5000);
    }
};