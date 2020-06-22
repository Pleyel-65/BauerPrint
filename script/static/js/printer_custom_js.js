function load_image() {
    var f = $('#files').prop('files')[0];
    var file_name = $('#files').val();

    if (f.type.split("/")[0] == "image"){
        var fReader = new FileReader();
        fReader.onload = function(event){
            var img = document.getElementById("yourImgTag");
            $('#photoContainer').attr('src', event.target.result);
            $('span.file-label').text(file_name.split("\\")[file_name.split("\\").length - 1]);
        }
        fReader.readAsDataURL(f);
    } else {
        console.log("Error! File must be an image");
    };
}
function sliders_event(){
    var new_val = $(this).val();
    if ($(this).attr('id') != "justificationSlider"){
        $(this).parent().find('span').text(new_val);
        $(this).parent().parent().parent().find('p').text(new_val);
    } else {
        switch ($(this).val()){
            case "0":
                $(this).parent().find('span').text("L");
                $(this).parent().parent().parent().find('p').text("L");
                break;
            case "1":
                $(this).parent().find('span').text("C");
                $(this).parent().parent().parent().find('p').text("C");
                break;
            case "2":
                $(this).parent().find('span').text("R");
                $(this).parent().parent().parent().find('p').text("R");
                break;
        }
    }
}
function clear_form(){
    $('#photoContainer').attr('src', "");
    $('span.file-label').text("No image");
    $('#textInput').val("");
    $("#alternateFontToggle").prop("checked", false);
    $("#emphasizeToggle").prop("checked", false);
    $("#underlineToggle").prop("checked", false);
    $("#doubleHeightToggle").prop("checked", false);
    $("#doubleWidthToggle").prop("checked", false);
    $("#fontSizeSlider").val(12);
    $("#justificationSlider").val(0);
    $("#cutToggle").prop('checked', false);
    $("#justificationSlider").trigger("input");
    $("#fontSizeSlider").trigger("input");
}

function send_printer_command() {
    var photo = $('#photoContainer').attr('src')

    var text_in = $('#textInput').val();

    var font_mode = 0;
    if ($("#alternateFontToggle").is(":checked")){
        font_mode += 1;
    };
    if ($("#emphasizeToggle").is(":checked")){
        font_mode += 8;
    };
    if ($("#underlineToggle").is(":checked")){
        font_mode += 128;
    };
    if ($("#doubleHeightToggle").is(":checked")){
        font_mode += 16;
    };
    if ($("#doubleWidthToggle").is(":checked")){
        font_mode += 32;
    };

    var font_size = $("#fontSizeSlider").val();
    var justification = $("#justificationSlider").val();
    var cut = $("#cutToggle").is(":checked") ? 1 : 0;

    var p_command = {
        text: text_in,
        set: {
            font_mode: font_mode,
            font_size: parseInt(font_size),
            justification: parseInt(justification),
        },
        cut: cut
    };
    if (photo != "") {
        p_command["image"] = photo;
    };

    $.ajax({
        type: "POST",
        url: "/print",
        dataType: "text",
        contentType: 'application/json',
        data: JSON.stringify(p_command),
        success: clear_form,
        error: function() {
            alert("Something went wrong with the server...");
        }
    });
}

$(document).ready(function(){
    $('input[type=range]').on('input', sliders_event);
    $('#files').on('input', load_image);
    $('#files').on('change', load_image);
    $("#printButton").click(send_printer_command);
});
