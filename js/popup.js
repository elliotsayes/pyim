function target_popup(form) {
    var margin_left = screen.width/2-400;
    var margin_top  = screen.height/2-300;
    window.open('', 'formpopup', 'width=800,height=600,toolbar=0,menubar=0,location=1,status=0,scrollbars=0,resizable=0,left='+margin_left+',top='+margin_top);
    form.target = 'formpopup';
}