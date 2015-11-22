 

$(document).ready(function(){

   $('code').each(function(i){
		var code_data=$(this).html();
		code_data=code_data.replace(/\t/g,"    ");
		$(this).html("<pre>"+code_data+"</pre>");
   });

   $('.edt_btn').each(function(i){
	   $(this).click(function() {
			var myid=$(this).attr('id');
			if(myid.match(/^edt_([a-z]+)$/i)){
				var pp=RegExp.$1;
				var addons="";
				var tail="</"+pp+">";
				if(pp=='a'){
					addons=" rel=\"nofollow\" href=\"\"";
				}else if(pp=='img'){
					addons=" src=\"\" border=\"0\" width=\"450\" /";
					tail="";
				}else if(pp=='nosizeimg'){
					pp="img";
					addons=" src=\"\" border=\"0\" /";
					tail="";
				}else if(pp=='source'){
					pp="a";
					addons=" rel=\"nofollow\" href=\"\"";
					tail="source</a>";
				}else if(pp=='aff'){
					pp="a";
					addons=" href=\"javascript:void(0);\" onclick=\"window.open('');\" rel=\"nofollow\"";
					tail="</a>";
				}
				
				//var select_data=$("#body").select();
				//if(select_data){
				//	insert_html('#body',"<"+pp+">"+select_data+"</"+pp+">");
				//}else{
					insertAtCaret('body',"<"+pp+addons+">"+tail);
				//}
			}
       });  
   });

   $('.del').click(function() {
	 var idstr=$(this).attr('id');
	 var mykey=$(this).attr('key');
	 if(idstr.match(/^did_([0-9]+)$/i)){
		var index=RegExp.$1;
		$.ajax({
		   type: "POST",
		   url: "/db",
		   data: "index="+index,
		   error: function(msg){
             alert('Failed to delete');
		   },
		   success: function(msg){
			 if(msg){
				 if(msg.err){
					alert('Error: '+msg.err);
				 }else{
					$('#entry_'+index).hide();
				 }
			 }else{
				alert('Please Login First.');
			 }
		   }
		 });
	 }
	 if(idstr.match(/^sdid_([0-9]+)$/i)){
		var index=RegExp.$1;
		var mykey2=0;
		if(mykey.match(/_([0-9]+)$/i)){
          mykey2=RegExp.$1;
		}
		$.ajax({
		   type: "POST",
		   url: "/sdb",
		   data: "index="+index+"_"+mykey2,
		   error: function(msg){
             alert('Failed to delete');
		   },
		   success: function(msg){
			 if(msg){
				 if(msg.err){
					alert('Error: '+msg.err);
				 }else{
					$('#entry_'+index).hide();
				 }
			 }else{
				alert('Please Login First.');
			 }
		   }
		 });
	 }
   });

   $('.msg').click(function() {
     var idstr=$(this).attr('id');
	 var mykey=$(this).attr('key');
	 if(idstr.match(/^sn_([0-9]+)$/i)){
       var index=RegExp.$1;
         $.ajax({
		   type: "GET",
		   url: "/eb",
		   data: "i="+index,
		   error: function(msg){
             alert('Failed to fetch');
		   },
		   success: function(msg){
			 if(msg){
				 if(msg.err){
					alert('Error: '+msg.err);
				 }else{
					var i=0;
                    if(msg[0].index){
						i=parseInt(msg[0].index);
						$('#editId').attr('value',i);
					}
					if(msg[0].title) $('#title').attr('value',msg[0].title);
					if(msg[0].body) $('#body').html(msg[0].body);
					if(msg[0].category) $('#category').attr('value',msg[0].category);
					if(msg[0].tag) $('#tag').attr('value',msg[0].tag);
					$('#myform').attr('action','/eb');
					$('#index').attr('value',i);
					$('#gosubmit').attr('value','Modify');
					$('#body').focus();
					createUploader();
				 }
			 }else{
				alert('Please Login First.');
			 }
		   }
		 });
		
	 }
	 if(idstr.match(/^ssn_([0-9]+)$/i)){
       var index=RegExp.$1;
         $.ajax({
		   type: "GET",
		   url: "/seb",
		   data: "i="+index+"&key="+mykey,
		   error: function(msg){
             alert('Failed to fetch');
		   },
		   success: function(msg){
			 if(msg){
				 if(msg.err){
					alert('Error: '+msg.err);
				 }else{
					var i=0;
                    if(msg[0].index){
						i=parseInt(msg[0].index);
						$('#editId').attr('value',i);
					}
					if(msg[0].title) $('#title').attr('value',msg[0].title);
					if(msg[0].body) $('#body').html(msg[0].body);
					$('#category').attr('value','');
					$('#tag').attr('value','');
					$('#myform').attr('action','/seb');
					$('#index').attr('value',i+'_'+msg[0].key);
					$('#gosubmit').attr('value','Modify');
					$('#body').focus();
					createUploader();
				 }
			 }else{
				alert('Please Login First.');
			 }
		   }
		 });
		
	 }
	 
   });

   $('.entry_detail img').each(function(){
		$(this).error(function() {
		  $(this).remove();
		});
   });


});

function insert_html(id,html){
	var text_data=$(id).val();
	$(id).val(text_data+"\n"+html);
}

function getSelected(trg){
	var t = '';
	if(window.getSelection){
		t = window.getSelection();
	}else if(document.getSelection){
		t = document.getSelection();
	}else if(document.selection){
		t = document.selection.createRange().text;
	}
	return t;
}

function insertAtCaret(areaId,text) { var txtarea = document.getElementById(areaId); var scrollPos = txtarea.scrollTop; var strPos = 0; var br = ((txtarea.selectionStart || txtarea.selectionStart == '0') ? "ff" : (document.selection ? "ie" : false ) ); if (br == "ie") { txtarea.focus(); var range = document.selection.createRange(); range.moveStart ('character', -txtarea.value.length); strPos = range.text.length; } else if (br == "ff") strPos = txtarea.selectionStart; var front = (txtarea.value).substring(0,strPos); var back = (txtarea.value).substring(strPos,txtarea.value.length); txtarea.value=front+text+back; strPos = strPos + text.length; if (br == "ie") { txtarea.focus(); var range = document.selection.createRange(); range.moveStart ('character', -txtarea.value.length); range.moveStart ('character', strPos); range.moveEnd ('character', 0); range.select(); } else if (br == "ff") { txtarea.selectionStart = strPos; txtarea.selectionEnd = strPos; txtarea.focus(); } txtarea.scrollTop = scrollPos; } 



