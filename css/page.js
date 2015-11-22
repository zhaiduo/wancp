
function checksearch(t){
	if(jQuery.trim(t.q.value)==""){
		var _self=$('#cse-search-box');
		zd_loading(_self);
		var _loading=$('.loading',_self);
		_loading.html(ajax_err('请输入关键词~'));
		close_loading(_loading,5000);
		return false;
	}else{
		return true;
	}
}

var t0= new Image(10,10); t0.src="/css/loading.gif";	
function zd_loading(target,type){
	var alert_id=".loading"
	if($(alert_id,target).length>0){
		$(alert_id,target).html("<img src=\"/css/loading.gif\">");
	}else{
		if(type=='pre'){
			$(target).prepend("<span class=\"loading\"><img src=\"/css/loading.gif\"></span>");
		}else{
			$(target).append("<span class=\"loading\"><img src=\"/css/loading.gif\"></span>");
		}
	}
}

function ajax_response(msg,ld){
	if(msg.error){
		ld.html(" "+ajax_msg(String(msg.error)));
		close_loading(ld,1000);
	}else if(String(msg).match(/^OK: (.+)$/i)){
		ld.html(" "+ajax_msg(RegExp.$1));
		close_loading(ld,1000);
	}else if(String(msg).match(/^Err: (.+)$/i)){
		ld.html(" "+ajax_err(RegExp.$1));
		close_loading(ld,5000);
	}else{
		alert(String(msg));
		close_loading(ld,5000);
	}
}

function close_loading(ld,t){
	if(typeof(t)=="undefined"){
		t=1000;
	}
	ld.fadeOut(t, function () {
		ld.remove();
	});
}

function ajax_msg(str){
	return "<font color=#008000>"+String(str)+"</font>";
}

function ajax_err(str){
	return "<font color=#ff0000>"+String(str)+"</font>";
}

function valid_email(email){
 	 if (!email.match(/^([0-9a-z\-\._]+)@([0-9a-z\-]+)\.([0-9a-z\-\.]+)$/ig)){
	 	return (false);
	 }else{
	 	return (true);
	 }
}
