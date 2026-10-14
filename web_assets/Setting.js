/*---------------------------------*
* Setting页面(5个)所共用的设置函数
* data->渲染当前页面所需数据（格式: {args:{},data:{}},args:{}包涵链接中data={}中的数据，data:{}包涵服务器返回的数据)
* fn->单击设置按钮后，调用的回调函数
*---------------------------------*/
Pages.Setting = function (data, fn) {
    var that = this;
    //focus某个input或keyup时,把当前值保存到Configs.setting['focus']里，只保存当前输入框的这个值，别的值不保存
    function SaveInputs(that) {
        var id = $(that).closest("ul").attr("id") || "ems_ul_id_145387964243";
        var $type = ($(that).attr("type") || that.nodeName).toLowerCase();
        if($type=="li"){
            id = $(that).parents("span").closest("ul").attr("id") || "ems_ul_id_145387964243";
        }
        if ($type == "fieldset") {
            $.each($(that).find(".radiodiv"),function(){
        		if($(this).prop("className")=="radiodiv"){
        		    Configs.Data.setting[id]=$(this).attr("value");
        		}
            });
        }else if($type == "text") {
            Configs.Data.setting[id] = that.value;
        }else{
            Configs.Data.setting[id] = $(that).find("a").attr("rel");
        }
        Configs.Data.setting['focus'] = id;
    }
    Pages.ReviseRadio();
    $("form").find(".set_value").off().on("click focus keyup", function () {
        SaveInputs(this);
    });
   $(".selectsp .input_select").next().find("li").on("click", function () {
        SaveInputs(this);
        $(this).blur();
    }).on("blur", function () {
        Configs.SelectFocus = null;
        Configs.Data.render = true;
    });
    $(".selectsp .dropdown").off().on("click", function (event) {
        if(event.target.className!=""){
            Configs.SelectFocus = $(this);
            Configs.Data.render = false;
        }
    })
    //自定义下拉列表事件
    Pages.BindSelect();
    //自定义单选按钮事件
    Pages.BindRadio();
    
     if(jQuery.cookie("systeminfo")!=1){
        if($("#Set_Fuse").length==0||$("#Set_ShuntsSystem").length==0){
            if($("#Set_Converter,#Set_mppt,#Set_Relay,#Set_PowerSystem,#Set_Rect,#Set_Charge").length>0){
                $(".table li").css({"padding-right":"50px"});
            }else{
                $(".table li").css({"padding-right":"60px"});
            }
        }
        $(".table-container,.extbackground").css({width:'1163px'});
	    $(".table-container .table,.table-title").css({width:"1143"});
    }else{
        $(".table li").css({"padding-right":"0px"});
        $(".table-container,.extbackground").css({width:'917px'});
        $(".table-title,.table-container .table").css({width:'897px'});
    }
    
    //记录当前正在输入的值,确保轮询更新时,该值不被清除，不影响用户的输入
    if (Control.isPolling) {
        //读取setting储存的值
        for (var id in Configs.Data.setting) {
            if (id == "focus") { continue; }
            if (id == Configs.Data.setting["focus"]) {
                var element = $("#" + id).find(".set_value");
                if (element[0]) {
                    var type = (element.attr("type") || element[0].nodeName).toLowerCase();
                } else {
                    break;
                }
                var value = Configs.Data.setting[id];
                switch (type) {
                    case "text":
                        element.val(value);
                        break;
                    case "div":
                        $(element[0]).attr("data-index",$(element[0]).next().find("li").eq(value).find("a").attr("rel")).text($(element[0]).next().find("li").eq(value).find("a").text());
                        break;
                    case "fieldset":
                        var iInputs = element.find("div.radiodiv");
                        var iType = (iInputs.eq(0).attr("type") || iInputs[0].nodeName).toLowerCase();
                        switch (iType) {
                            case "div":
                                if(iInputs.eq(value).hasClass("radiodivnot")){
                                    iInputs.eq(value).removeClass("radiodivnot");
                                    iInputs.not(iInputs.eq(value)).addClass("radiodivnot");
                                }
                                break;
                        }
                        break;
                    default:
                        element.val(Configs.Data.setting[id]);
                }
            } else {
                Configs.Data.setting[id] = null;
                delete Configs.Data.setting[id];
            }
        };
        //鼠标定位当前操作元素,如果是text，则光标定位在值最后
        var focus_input = $("#" + Configs.Data.setting['focus']).find(".set_value");
        if (focus_input[0] && Configs.HighLight) {
            var focus_type = (focus_input.attr("type") || focus_input[0].nodeName).toLowerCase();
            var focus_value = Configs.Data.setting[Configs.Data.setting['focus']];
            //focus时定位光标在字符串最后面
            switch (type) {
                case "text":
		    that.moveCursorToEnd(focus_input[0]);
                    break;
                case "div":
                    $(element[0]).attr("data-index",$(element[0]).next().find("li").eq(value).find("a").attr("rel")).text($(element[0]).next().find("li").eq(value).find("a").text());
                    break;
                case "fieldset":
                    var iInputs2 = element.find("div.radiodiv");
                    var iType2 = (iInputs2.eq(0).attr("type") || iInputs2[0].nodeName).toLowerCase();
                    switch (iType) {
                         case "div":
                            if(iInputs.eq(value).hasClass("radiodivnot")){
                                iInputs.eq(value).removeClass("radiodivnot");
                                iInputs.not(iInputs.eq(value)).addClass("radiodivnot");
                            }
                            break;
                    }
                    break;
                default:
		that.moveCursorToEnd(focus_input[0]);
            }
            Configs.Backspace = false;
        };
    } else {
        //如果不是轮询状态,清空Configs.Data.setting;
        for (var id in Configs.Data.setting) {
            delete Configs.Data.setting[id];
        };
    };
    //mouseover,mouserout鼠标经过事件
    var uls = $("div.table-body ul");
    $("div.table-body").off("click").on("click", "a.btn_set", function () {
        if ($(this).hasClass("btn_set_disabled")) { return false; }
        var SetProgress = document.getElementById("SetProgress");
        if (SetProgress) { $(SetProgress).remove(); }
        Configs.Backspace = false;
        //单击按钮提交当前行设置
        var form = $(this).closest("form"),
                action = form.attr('action'),
                type = form.attr('method'),
                item = $(this).closest("ul"),
                post = $(this).attr("post"),
                input = item.find(".set_value"),
                input_type = (input.attr("type") || input[0].nodeName).toLowerCase()
                var value="";
                if(input_type == "fieldset"){ 
                    $.each(item.find(".radiodiv"),function(){
                		if($(this).prop("className")=="radiodiv"){
                		    value=$(this).attr("value");
                		}
                	}); 
                }else if(input_type=="div"){
                    value =input.attr("data-index");
                }else{ 
                    value = input.val()
                }
        //对控制信号的提示
        var ControlTip = "";
        try {
            ControlTip = jQuery.evalJSON($(this).attr("tip"))[value][jQuery.cookie("language_type")];
        } catch (e) { }
        if (!ControlTip) {
            ControlTip = Language.Html["037"];
        }
        //高亮当前设置的行
        uls.removeClass("select");
        item.addClass("select");
        Configs.HighLight = item.attr("id");
	var isControlSignal = $(this).hasClass("set_control");
        if (isControlSignal) {
            if (!confirm(ControlTip)) {
                return false;
            }
        }
        try {
            var validate = jQuery.evalJSON(input.attr("validate"));
        } catch (err) {
            alert(Language.Html["031"]);
            return false;
        }

        //如果当前输入的值和已经设置的值一样，则提示没必须再设置,则不发送设置请求
        var btn_value = $(this).attr("value");
        if (btn_value && value == btn_value && !isControlSignal) {
            alert(Language.Validate['004']);
            return false;
        };
        var restart = false;
        if ($(this).hasClass("set_RectifierExpansion")) {
            restart = true;
        };
        if (restart) {
            if (!confirm(Language.Html["045"] + " \"" + input.find("option:selected").text() + "\", " + Language.Html["046"])) {
                return false;
            }
        };
        //如果input的validate属性存在，则依此进行验证输入的是否正确
        if (validate) {
            if (!validate.reg) {
                if (input_type == "text") {
                    if (!Validates.CheckSetting(input, validate, value)) {
                        return false;
                    }
                }
            }
        }
        var wait = [false, 0];
        var btn_wait = $(this).attr("wait");
        if (btn_wait && btn_wait != "") {
            var waitTime = 30;
            if (Number(btn_wait) > 0) {
                waitTime = Number(btn_wait);
            }
            wait = [true, waitTime];
        }
        //提交设置请求给SettingSubmit方法
        that.SettingSubmit({
            "args": data.args,
            "action": action,
            "item": item,
            "post": post,
            "type": type,
            "fn": fn,
            "restart": restart,
            "wait": wait,
			"btn":$(this)
        });
        return false;
    }).on("click", "ul", function () {
        //单击当前行的时候，高亮当前行
        uls.removeClass("select");
        $(this).addClass("select");
        Configs.HighLight = $(this).attr("id");
    });
};
    /*---------------------------------*
    * 提交Setting相关页面的设置
    *---------------------------------*/
Pages.SettingSubmit = function (data) {
    var that = this;
    //调用设置弹出框
    this.SetProcess(Language.Html['011']);
    var currentEle = data.item.find(".set_value");
    var currentEleLen = currentEle.length;
    var dataStr = "";
    if (currentEleLen > 0) {
        for (var z = 0; z < currentEleLen; z++) {
            var type = (currentEle.eq(z).attr("type") || currentEle.eq(z)[0].nodeName).toLowerCase();
            var pname = $.trim(currentEle.eq(z).attr("pname"));
            if (!pname || pname == "") {
                dataStr += "control_value=";
            } else {
                dataStr += (z > 0 ? "&" : "") + pname + "=";
            }
            switch (type) {
                case "text":
                case "select":
                case "select-one":
                case "textarea":
                    //如果设置按钮的样式有"set_plan"，则转化时间
                    if (currentEle.eq(z).hasClass("set_plan")) {
                        var mdh = currentEle.eq(z).val().replace("-", " ").split(" ");
                        for (var i = 0, ilen = mdh.length; i < ilen; i++) {
                            if (mdh[i].length < 2) {
                                mdh[i] = Validates.MakeupZero(mdh[i]);
                            }
                        }
                        var s_time = Validates.GetNoTimeZoneTime("1972/" + mdh[0] + "/" + mdh[1] + " " + mdh[2] + ":07:30");
                        dataStr += s_time;
                    } else {
                        dataStr += encodeURIComponent(currentEle.eq(z).val());
                    }
                    break;
                case "fieldset":
                    var iInputs = currentEle.eq(z).find("div");
                    var iType = (iInputs.eq(0).attr("type") || iInputs[0].nodeName).toLowerCase();
                    switch (iType) {
                        case "div":
                            for (var i = 0, ilen = iInputs.length; i < ilen; i++) {
                                if (iInputs.eq(i).prop("className")=="radiodiv") {
                                    dataStr += encodeURIComponent(iInputs.eq(i).attr("value"));
                                }
                            }
                            break;
                        case "checkbox":
                            value = [];
                            for (var i = 0, ilen = iInputs.length; i < ilen; i++) {
                                if (iInputs.eq(i).prop("checked")) {
                                    value.push(iInputs.eq(i).val());
                                }
                            }
                            dataStr += encodeURIComponent(value.join(","));
                            break;
                    };
                    break;
                case "div":
						dataStr += encodeURIComponent(currentEle.attr("data-index"));
                break;
            };
        };
    };
    if (data.post) {
        dataStr += "&" + data.post;
    };
    dataStr += "&sessionId=" + data.args["sessionId"];
    var set_site = false;
    if (/set_type=site/g.test(dataStr)) {
        dataStr.replace("set_type=site&", "");
        set_site = true;
    };
    var args = data;
    sendSubmit(dataStr, data["fn"]);
    function sendSubmit(submitData, fn) {
        //初始设置过程“开始”状态
        that.SetProcessStart();
        var XHR = $.ajax({
        	//changed by Frank Wu,20140513, for SMDUH signals timeout
        	//timeout: 10000, //设置页面，超时时间更改为10秒
        	timeout: 20000, //设置页面，超时时间更改为20秒
            url: data.action + "?_=" + new Date().getTime(),
            type: data.type,
            data: submitData,
            success: function (data, textStatus, jqXHR) {
                try {
                    var data = jQuery.evalJSON(data);
                } catch (err) {
                    that.SetProcessDone(Language.Html["001"]);
                    return false;
                }
                if (data.status == 98) {
                    that.SetProcessDone(Language.Html['019'] + Configs.Prompt.relogin);
                    return;
                }
                if (data.status != 1 && data.status != 6) {
                    that.SetProcessDone(Language.Setting[data.status]);
                } else if (data.status == 6) {
                    that.SetProcessDone(Language.Setting[data.status] + Configs.Prompt.relogin, sendSubmit, dataStr);
                }
                if (data.status == 1) {
                    if (args.restart) {
                        that.DoRestart();
                        return false;
                    };
                    if (set_site) {
                        $("#HeaderSiteName").html(data.content[0][2]);
                        $("#HeaderSiteLocation").html(data.content[1][2]);
                        $("#SideSite").html(data.content[2][2]);
                    }
                    if (args.wait && args.wait[0]) {
                        args.wait[1] = args.wait[1] > 0 ? args.wait[1] : 30;
                        that.DoRestart(false, args.wait[1], Language.Setting[data.status] + Language.Html['053'], function () {
                            that.SetProcessRemove();
                        })
                    } else {
                        //调用设置"OK"状态
                        that.SetProcessOK(Language.Setting[data.status]);
						var thisBtn = args.btn;
						//更新按钮的值
						if(thisBtn[0]){
							var cvalue = currentEle.attr("data-index");
							var inputType = (currentEle.attr("type") || currentEle[0].nodeName).toLowerCase();
							switch(inputType){
								case "fieldset":
									$.each(currentEle.find(".radiodiv"),function(){
        		                        if($(this).prop("className")=="radiodiv"){
        		                           cvalue=$(this).attr("value");
        		                        }
                                    });
									break;
							}
							thisBtn.attr('value',cvalue);
						}
			            //更新系统时间
			            var SignalID = args.item[0].id;
			            if(/1_2_456_/g.test(SignalID)){
				          Configs.TimeFormat = cvalue;
				          Pages.footer();
			            }
                    }
                    //赋值
                    for (var id in Configs.Data.setting) {
                        delete Configs.Data.setting[id];
                    };
                    //执行回调函数
                    if (fn && $.type(fn) === "function") {
                        fn();
                    };
                }
            },
            error: function (data, textStatus) {
                if (args.restart) {
                    that.DoRestart();
                    return false;
                };
                that.SetProcessDone(Language.Html['016'] + Language.Html["055"], sendSubmit, dataStr);
            }
        }).always(function (jqXHR, textStatus, errorThrown) {
            jqXHR = null;
            textStatus = null;
            errorThrown = null;
            XHR = null;
        })
    };
};