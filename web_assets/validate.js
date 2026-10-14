/*!
 * Author: Jerman.Xie | xieguishi@126.com
 * Date: 2013.09
 * 
 * Form表单验证
 */
var Validates = {
    /*
    * 对日期操作,月、日、分、秒、毫秒不足10时，补0
    */
    MakeupZero: function (num) {
        if (num == 0) {
            return "00";
        }
        if (num < 10) {
            return "0" + num;
        } else {
            return num;
        }
    },
    Atoi: function (str) {
        if (isNaN(str)) {
            return 0;
        };
        var s1 = "", i, c;
        // skip 0 before a decimal string  
        for (i = 0; i < str.length; i++) {
            c = "" + str.charAt(i);
            if (c != "0") {
                break;
            }
        };
        if (i == str.length) {
            return 0;
        };
        for (; i < str.length; i++) {
            s1 = s1 + str.charAt(i);
        };
        return parseInt(s1);
    },
    /*
    * 将整型数据转换成"nn.nn.nn.nn"形式的IP格式
    */
    ConvertIP: function (ip) {
        if (isNaN(ip)) {
            ip = this.Atoi(ip);
        };
        var strIP = "" + ((ip) & 0xff) + "." + ((ip >> 8) & 0xff) + "." + ((ip >> 16) & 255) + "." + ((ip >> 24) & 255);
        return strIP;
    },
    /*
    * 将"nn.nn.nn.nn"形式的IP格式转换成长整型
    */
    ParseIntIP: function (ip) {
        if (!this.CheckIP(ip)) {
            return 0;
        }
        var myArray = ip.split(/\./);
        var ip = 0, i;
        for (i = 0; i < 4; i++) {
            ip <<= 8;
            ip += this.Atoi(myArray[i]);
        }
        return ip;
    },
    CheckIP: function (what, zero) {
        //what->传进来的ip
        //zero->是否允许为0,true表示允许,false表示不允许,默认为不允许
        if (what.search(/^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$/) == -1) {
            return false;
        }
        var myArray = what.split(/\./);
        var CheckZero = false;
        for (var i = 0; i < 4; i++) {
            if (!CheckZero) {
                if (myArray[i] > 0) {
                    CheckZero = true;
                }
            }
            if (isNaN(myArray[i])) {
                return false;
            }
            var t = this.Atoi(myArray[i]);
            if ((t < 0) || (t > 255)) {
                return false;
            }
        }
        if (!zero) {
            if (!CheckZero) {
                return false;
            }
        }
        return true;
    },
    CheckIPV6: function (ipv6,port) {
		if(!ipv6){ return false; }
		ipv6 = $.trim(ipv6);
        var reg = /(^\s*((([0-9A-Fa-f]{1,4}:){7}([0-9A-Fa-f]{1,4}|:))|(([0-9A-Fa-f]{1,4}:){6}(:[0-9A-Fa-f]{1,4}|((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){5}(((:[0-9A-Fa-f]{1,4}){1,2})|:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3})|:))|(([0-9A-Fa-f]{1,4}:){4}(((:[0-9A-Fa-f]{1,4}){1,3})|((:[0-9A-Fa-f]{1,4})?:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){3}(((:[0-9A-Fa-f]{1,4}){1,4})|((:[0-9A-Fa-f]{1,4}){0,2}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){2}(((:[0-9A-Fa-f]{1,4}){1,5})|((:[0-9A-Fa-f]{1,4}){0,3}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(([0-9A-Fa-f]{1,4}:){1}(((:[0-9A-Fa-f]{1,4}){1,6})|((:[0-9A-Fa-f]{1,4}){0,4}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:))|(:(((:[0-9A-Fa-f]{1,4}){1,7})|((:[0-9A-Fa-f]{1,4}){0,5}:((25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)(\.(25[0-5]|2[0-4]\d|1\d\d|[1-9]?\d)){3}))|:)))(%.+)?\s*$)/gi;
		if(port){
			if(ipv6[0]!=="[" || !(/\]:/g.test(ipv6))){
				return false;
			}
			var ip = ipv6.split("]:"),port = parseInt(ip[1]);
			ipv6 = ip[0].replace("[","");
			if(!reg.test(ipv6) || (ip[1] =="" || port < 0 || port > 65534)){
				return false;
			}
		} else {
			if(!reg.test(ipv6)){
				return false;
			}
		}
        return true;
    },

    MakeTimeZoneInfo: function (nTimeZone) {//unit is seconds
        var nTZ, buf;
        if (isNaN(nTimeZone)) {
            nTimeZone = -28800; //china
        };
        buf = "GMT";
        buf += "" + ((nTimeZone > 0) ? '-' : '+');
        nTZ = (nTimeZone > 0) ? nTimeZone : -nTimeZone;
        var hr = Math.floor(nTZ / 3600);
        var mn = Math.floor((nTZ % 3600) / 60);
        buf += "" + ((hr >= 10) ? hr : "0" + hr) + ":" + ((mn >= 10) ? mn : "0" + mn);
        return buf;
    },
    ParseTimeZoneInfo: function (zi) {
        var nSign, nHr = 0, nMin = 0, i;
        /* GMT+hh:mm */
        if ((zi == null) || (zi.length == 0)) { return -1; };
        if ((zi.charAt(0) != "G") && (zi.charAt(0) != "g") && (zi.charAt(1) != 'M') && (zi.charAt(1) != 'm') && (zi.charAt(2) != 'T') && (zi.charAt(2) != 't')) {
            return -1;
        };
        if (zi.length == 3) { return 0; };  /* GMT standard time */
        /* sign */
        if (zi.charAt(3) == '+') {
            nSign = -1;
        } else if (zi.charAt(3) == '-') {
            nSign = +1;
        } else {
            return -1;
        }
        /* hrs */
        i = 4;
        var c = zi.charAt(i);
        if ((c >= "0") && (c <= "9")) {
            nHr = parseInt(c);
            i++;
        } else {
            return -1;
        };
        c = zi.charAt(i);
        if ((c >= "0") && (c <= "9")) {
            nHr = nHr * 10 + parseInt(c);
            i++;
        };
        if (nHr >= 24) { return -1; };
        if (zi.length == i) { /* no min. */return nSign * nHr * 3600; };
        if (zi.charAt(i) != ':') { return -1; };
        /* min. */
        i++;
        c = zi.charAt(i);
        if ((c >= "0") && (c <= "9")) {
            nMin = parseInt(c);
            i++;
        } else {
            return -1;
        };
        c = zi.charAt(i);
        if ((c >= "0") && (c <= "9")) {
            nMin = nMin * 10 + parseInt(c);
            i++;
        };
        if (nMin >= 60) { return -1; };
        return nSign * (nHr * 3600 + nMin * 60);
    },
    CheckDate: function (obj) {
        var monthDay = new Array(31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31);
        var month, day, year, retval = false;
        if (obj == "") {
            return false;
        };
        obj = $.trim(obj);
        if (obj != "") {
            //check  of string 
            var a = obj.split("/");
            if (a.length == 3 && a[0] != "" && a[1] != "" && a[2] != "") {
                if (a[0].length > 4 || a[1].length > 2 || a[2].length > 2) {
                    return false;
                }
                // Month must be between 1 and 12  
                month = a[1];
                var t = this.Atoi(month);
                if (!isNaN(month) && t > 0 && t <= 12) {
                    month = t;
                    year = a[0];
                    // limit year to range 1900 - 2100 
                    if (!isNaN(year) && this.Atoi(year) >= 1900 && this.Atoi(year) <= 9999) {
                        day = a[2];
                        if (!isNaN(day)) {
                            day = this.Atoi(day);
                            t = monthDay[month - 1];
                            if (month == 2)
                                t += this.CheckLeapYear(year);
                            if (day > 0 && day <= t) {
                                retval = true;
                            }
                        }
                    }
                }
            }
        }
        return retval;
    },
    CheckTime: function (obj) {
        if (obj == "") {
            return false;
        };
        obj = $.trim(obj);
        var a = obj.split(":");
        if (a.length > 3) { return false; };
        var hours = a[0];
        var minutes = a.length >= 2 ? a[1] : "0";
        var seconds = a.length > 2 ? a[2] : "0";
        if ((hours.length > 2) || (hours.length == 0) || (minutes.length > 2) || (minutes.length == 0) || (seconds.length > 2) || (seconds.length == 0)) { return false; }
        // Hours must be between 0 and 24  
        var t = this.Atoi(hours);
        if (!isNaN(hours) && t >= 0 && t < 24) {
            if (!isNaN(minutes)) {
                minutes = this.Atoi(minutes);
                if (minutes >= 0 && minutes <= 59) {
                    // seconds between 0 and 59 
                    t = this.Atoi(seconds);
                    if (!isNaN(seconds) && t >= 0 && t <= 59) {
                        return true;
                    }
                }
            }
        }
        return false;
    },
    CheckDateTime: function (target) {
        var time = $(target).val();
        if (!/ /gi.test(time)) { return false; }
        var date_time = time.split(" ");
        var new_date = [];
        //去除多余的空格
        for (var i = 0, ilen = date_time.length; i < ilen; i++) {
            if (date_time[i] != "") {
                new_date.push(date_time[i]);
            }
        }
        $(target).val(new_date.join(" "));
        if (this.CheckDate(new_date[0]) && this.CheckTime(new_date[1])) {
            return true;
        }
        return false;
    },
    CheckLeapYear: function (year) {
        var y = 0;
        if ((year % 4 == 0) && !(year % 400 != 0 && year % 100 == 0)) {
            y = 1;
        };
        return y;
    },
    CheckSetting: function (input, validate, value) {
        var value = $.trim(value);
        //validate是对象
        switch (validate.type) {
            /*int,正整数和0*/
            case 1:
                if (value == "") {
                    alert(Language.Validate['001']);
                    input.focus();
                    return false;
                } else if (isNaN(value) || !(/^[0-9]*[^\.][0-9]*$/gi.test(value))) {
                    alert(Language.Validate['002_int']);
                    input.focus();
                    return false;
                } else if (value < validate.range[0] || value > validate.range[1]) {
                    alert(Language.Validate['003']);
                    input.focus();
                    return false;
                }
                break;
            /*float,浮点数*/
            case 2:
                if (value == "") {
                    alert(Language.Validate['001']);
                    input.focus();
                    return false;
                } else if (isNaN(value)) {
                    alert(Language.Validate['002_float']);
                    input.focus();
                    return false;
                } else if (value < validate.range[0] || value > validate.range[1]) {
                    alert(Language.Validate['003']);
                    input.focus();
                    return false;
                }
                break;
            /*unsigned int,正负整数或0*/
            case 3:
                if (value == "") {
                    //Control.PromptEvent.Alert(Language.Validate['001']);
                    alert(Language.Validate['001']);
                    input.focus();
                    return false;
                } else if (isNaN(value) || !(/^-*[0-9]*[^\.][0-9]*$/gi.test(value))) {
                    alert(Language.Validate['002_unsigned_int']);
                    input.focus();
                    return false;
                } else if (value < validate.range[0] || value > validate.range[1]) {
                    alert(Language.Validate['003']);
                    input.focus();
                    return false;
                }
                break;
            /*time,时间*/
            case 4:
                if (value == "") {
                    alert(Language.Validate['001']);
                    input.focus();
                    return false;
                } else {
                    if (validate.date) {
                        var value = $.trim(value).replace(/-/g, " ").split(" ");
                        var newValue = [];
                        for (var item in value) {
                            if (value[item] != "") {
                                newValue.push(value[item]);
                            }
                        }
                        value = newValue;
                        if (value.length > 3) {
                            alert(Language.Validate["007"]);
                            return;
                        }
                        var validate = validate.date.split("-");
                        var isChecked = false;
                        if (value.length == validate.length) {
                            //检测是否是有效时间
                            if (!this.CheckDate("2008/" + value[0] + "/" + value[1])) {
                                alert(Language.Validate["007"]);
                                return;
                            }
                            for (var i = 0, ilen = validate.length; i < ilen; i++) {
                                if (validate[i] == "mm") {
                                    if (value[i] < 1 || value[i] > 12) {
                                        alert(Language.Validate["007"]);
                                        isChecked = true;
                                        break;
                                    }
                                } else if (validate[i] == "dd") {
                                    if (value[i] < 1 || value[i] > 31) {
                                        alert(Language.Validate["007"]);
                                        isChecked = true;
                                        break;
                                    }
                                } else if (validate[i] == "hh") {
                                    if (value[i] < 0 || value[i] > 23) {
                                        alert(Language.Validate["007"]);
                                        isChecked = true;
                                        break;
                                    }
                                }
                            };
                            if (isChecked) {
                                return false;
                            }
                        } else {
                            alert(Language.Validate["007"]);
                            return false;
                        }
                    }
                }
                break;
            /*enum,数字*/
            case 5:
                break;
            case "sitename":
                if (value == "") {
                    alert(Language.Validate['001']);
                    input.focus();
                    return false;
                } else {
                    /*匹配所有东亚语言和英文数字,且不能设置纯数字*/
                    //var reg = /^([\u2E80-\u9FFF]|[a-zA-Z])+[0-9]*([\u2E80-\u9FFF]|[a-zA-Z])*$/;
                    var reg = /["\/<>&#!\\]/g;
                    if (reg.test(value)) {
                        alert(Language.Validate['008']);
                        return false;
                    }
                }
                break;
        };
        return true;
    },
    //验证正则是否通过
    CheckReg: function (input, reg, text) {
        var reg = new RegExp(reg);
        if (!reg.test(input.val())) {
            alert(text);
            input.focus();
            return false;
        }
        return true;
    },
    /*---------------------------------*
    * 检测信号值的有效性
    * 格式：["value","alarm_state","unvalid_state","not_config_state"]
    * value就是以前的值；
    * alarm_state表示告警状态，1需要变红显示，0正常显示；
    * unvalid_state表示是否有效，1需要反白显示，0正常显示；
    * not_config_state表示是否配置，1需要隐藏，0正常显示；
    * relation =>false表示data1和data2为||，否则为&&
    * show => 为true表示，显示为"---"且不隐藏 
    *---------------------------------*/
    CheckValue: function (data1, data2, relation, show) {
        if (data1 && $.type(data1) != "array") { return ""; }
        //if (data2 && $.type(data2) != "array") { return ""; }
        var v_class = "";
        //data[0]为avalue值μ不?作痢耚uinput2判D断?
        //1->v_alarm;
        //2->v_disabled;
        //3->v_hidden;
        function GetColor(d) {
            var vclass = "";
            if (d[1] == 1) {
                vclass = 1;
            }
            if (d[2] == 1) {
                vclass = 2;
            }
            if (d[3] == 1) {
                vclass = 3;
            }
            return vclass;
        }
        var v1_class = GetColor(data1);
        var v2_class = -1;
        if (data2) {
            v2_class = GetColor(data2);
            if (!relation) {
                //or
                if (v1_class == 1 || v2_class == 1) {
                    v_class = "v_alarm";
                }
                if (v1_class == 2 || v2_class == 2) {
                    v_class = "v_disabled";
                }
                if (v1_class == 3 || v2_class == 3) {
                    if (data2 === true) {
                        v_class = "";
                    } else {
                        v_class = "v_hidden";
                    }
                }
            } else {
                //and
                if (v1_class == 1 && v2_class == 1) {
                    v_class = "v_alarm";
                }
                if (v1_class == 2 && v2_class == 2) {
                    v_class = "v_disabled";
                }
                if (v1_class == 3 && v2_class == 3) {
                    if (show === true) {
                        v_class = "";
                    } else {
                        v_class = "v_hidden";
                    }
                }
            }
        } else {
            if (v1_class == 1) {
                v_class = "v_alarm";
            }
            if (v1_class == 2) {
                v_class = "v_disabled";
            }
            if (v1_class == 3) {
                v_class = "v_hidden";
            }
        }
        return v_class;
    },
    CheckValueReturn: function (value, unit,ins) {
        if (!value) { return; }
        var cla = this.CheckValue(value);
        if (cla == "v_disabled") {
            return !ins ? "<ins class='v_disabled'>---</ins>" : "---";
        } else if (cla == "v_hidden") {
            return !ins ? "<ins>---</ins>" : "---";
        } else if (cla == "v_alarm") {
            return !ins ? "<ins class='v_alarm'>" + (value[0] || value || "") + (unit ? unit : "") + "</ins>" : (value[0] || value || "") + (unit ? unit : "");
        } else {
            return (value[0] || value || "") + (unit ? unit : "");
        }
    },
    //匹配所有数字和#
    MatchNumber: function (str) {
        return str.match(/[\d#]/g).join("");
    },
    //只匹配数字
    MatchNum: function (str) {
        return str.match(/[\d]/g).join("");
    },
    //从机模式，匹配所有数字和#
    MatchNumberS: function (str) {
        return str.match(/[\d#]/g).join("");
        //return str.replace(/[\d#]/, "").match(/[\d#]/g).join("");
    },
    GetNoTimeZoneTime: function (date) {
        var newdt = new Date();
        newdt.setFullYear(date.substr(0, 4));
        newdt.setDate(date.substr(8, 2));
        newdt.setMonth(date.substr(5, 2) - 1);
        newdt.setHours(date.substr(11, 2));
        newdt.setMinutes(date.substr(14, 2));
        newdt.setSeconds(date.substr(17, 2));
        //Not need timezone
        return Math.floor((newdt.getTime() - newdt.getTimezoneOffset() * 60000) / 1000);
    },
    SetBatteryTime: function (nSec) {
        function makeSampleDateStr(nSec) {
            return "" + getSampleCurUTCDate(nSec) + " " + getCurUTCTime(nSec);
        }
        function getSampleCurUTCDate(nSec) {
            if (isNaN(nSec)) {
                nSec = this.atoi(nSec);
                if (isNaN(nSec))
                    nSec = 0;
            }
            var s = "-";
            var d = new Date();
            if (nSec != 0) {
                d.setTime(nSec * 1000);
            }
            var dd = d.getUTCDate();
            var sd = (dd < 10) ? "0" + dd : "" + dd;
            var m = d.getUTCMonth() + 1;
            var sm = (m < 10) ? "0" + m : "" + m;
            var strDate = "" + d.getUTCFullYear() + s + sm + s + sd;
            return strDate;
        }
        function getCurUTCTime(nSec) {
            if (isNaN(nSec)) {
                nSec = this.atoi(nSec);
                if (isNaN(nSec))
                    nSec = 0;
            }
            var c = ":";
            var d = new Date();
            if (nSec != 0) {
                d.setTime(nSec * 1000);
            }
            var s = d.getUTCSeconds();
            var ss = (s < 10) ? "0" + s : "" + s;
            var m = d.getUTCMinutes();
            var sm = (m < 10) ? "0" + m : "" + m;
            var h = d.getUTCHours();
            var sh = (h < 10) ? "0" + h : "" + h;
            var strTime = "" + sh + c + sm + c + ss;
            return strTime;
        }
        function getShowFormat(varTime) {
            var varFormat1;
            varFormat1 = varTime.substring(5, 13);
            return varFormat1;
        }
        var varTempTime;
        if (nSec > 0) {
            varTempTime = makeSampleDateStr(nSec);
        } else {
            varTempTime = makeSampleDateStr(63072450);
        }
        varValue = getShowFormat(varTempTime);
        return varValue;
    },
	/* 验证email邮箱
	 * obj-> 目标验证值,必选项,可以为一个input DOM，也可为一个值
	 * reg-> 自定义验证邮箱的正则表达式
	*/
	CheckEmail: function(obj,reg) {
		if(!obj){ return false; }
        var reg_mail = $.type(reg)=="regexp" ? reg : /^(\.*[a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+((\.[a-zA-Z0-9_-]{2,100}){1,2})$/gi;
		if($.type(obj)=="string"){
			if (!reg_mail.test(obj)) {
				return false;
			}
		} else {
			if (!reg_mail.test(obj.val())) {
				if($(obj)[0]){
					obj[0].select();
				}
				return false;
			}
		}
        return true;
    }
};