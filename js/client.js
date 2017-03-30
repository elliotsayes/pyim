
target = "";
scrollNext = true;

/* get FL update from server every 15s */
(function updateFL() {
    $( "#friendslist" ).load( "jsGetUsers" );
    setTimeout(updateFL, 15000);
})();

/* send report to server every 50s */
(function keepAlive() {
    $.get( "jsAlive" );
    setTimeout(keepAlive, 50000);
})();

/* get any new messages from database every 1s */
/* ONLY if the chat window is scrolled to the bottom, autoscroll down when receiving a new message */
(function updateMessages() {
	scrollThis = scrollNext;
	scrollNext =  $( "#messages" ).scrollTop() == ( $( "#messages" )[0].scrollHeight - $("#messages").height())
    $( "#messages" ).load( "jsGetMessages?chatID=" + target );
	if(scrollThis) {$( "#messages" ).scrollTop($( "#messages" )[0].scrollHeight);}
    setTimeout(updateMessages, 1000);
})();

/* send message when button is clicked, show error alert if unsuccessful */
$("button#send_message").click(function(){
    $.get( "jsSend?targetID=" + target + "&message=" + $("#message_content").val(), function(data) {
		if(data != "0") {alert("message not sent!\error: " + data );}
	});
	$( "#message_content" ).val("");
});

function setTarget(targetID) {
    target=targetID;
    scrollNext = true;
}
