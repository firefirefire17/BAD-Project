$('[id$="-button"]').on("click", function (e) {
    var color = $(this).attr('data-color');
    var colorBackdrop = 'modal-backdrop-' + color;
    // alert(color);
    $('#modal-backdrop').addClass(colorBackdrop);
});
$('.btn-close, .modal').on("click", function (e) {
    var color = $('.in').attr('data-color');
    var activeBackdrop = 'modal-backdrop-' + color;
    $('#modal-backdrop').removeClass(activeBackdrop);
});

$("button[data-dismiss-modal=confirm-modal]").click(function () {
    $('#confirm-modal').modal('hide');
});