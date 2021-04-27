$(function(){
     $('.menu_open, .menu a').click(function () {
     $('.menu_collapse').toggleClass('d-none').css('order', '1');
     $('.menu').toggleClass('menu_opened');
    });

     $(document).ready(function() {
        $('[data-submit]').on('click', function(e) {
        e.preventDefault();
        $(this).parent('form').submit();
    })
    $.validator.addMethod(
        "regex",
        function(value, element, regexp) {
            let re = new RegExp(regexp);
            return this.optional(element) || re.test(value);
        },
        "Please check your input."
    );

    function valEl(el) {
        el.validate({
            rules: {
                customer_tel: {
                    required: true,
                    regex: '^([\+]+)*[0-9\x20\x28\x29\-]{5,20}$'
                },
                customer_name: {
                    required: true
                },
                customer_email: {
                    required: true,
                    email: true
                }
            },
            messages: {
                customer_tel: {
                    required: 'Поле потрібно заповнити',
                    regex: 'Телефон може містити символи + - ()'
                },
                customer_name: {
                    required: 'Поле потрібно заповнити',
                },
                customer_email: {
                    required: 'Поле потрібно заповнити',
                    email: 'Не вірний формат E-mail'
                }
            },
            submitHandler: function(form) {
                    $('#loader').fadeIn();
                    let $form = $(form);
                    let $formId = $(form).attr('id');
                    if ($formId == "popupResult") {
                            $.ajax({
                                    type: 'POST',
                                    url: $form.attr('action'),
                                    data: $form.serialize(),
                                })
                                .always(function(response) {
                                    setTimeout(function() {
                                        $('#loader').fadeOut();
                                    }, 800);
                                    setTimeout(function() {
                                        $('#overlay').fadeIn();
                                        $form.trigger('reset');
                                    }, 1100);
                                    $('#overlay').on('click', function(e) {
                                        $(this).fadeOut();
                                    });

                                });
                    }
                    return false;
            }
        })
    }
    $('.js-form').each(function() {
        valEl($(this));
    });

});

    $('.slider').slick({
        slidesToShow: 1,
        slidesToScroll: 1,
        autoplay: true,
        autoplaySpeed: 2000,
        prevArrow: '<button type="button" class="slick-prev"><i class="fas fa-arrow-left"></i></button>',
        nextArrow: '<button type="button" class="slick-next"><i class="fas fa-arrow-right"></i></button>',
    });

    $(window).scroll(function() {
        $('.free_psd_p').each(function(){
            let imagePos = $(this).offset().top;
            let topOfWindow = $(window).scrollTop();
            if (imagePos < topOfWindow+850) {
                $(this).addClass("animate__fadeInUp");
            }
        });
        $('.free_psd_p2').each(function(){
            let imagePos = $(this).offset().top;
            let topOfWindow = $(window).scrollTop();
            if (imagePos < topOfWindow+850) {
                $(this).addClass("animate__fadeInUp");
            }
        });
        $('.free_psd_h3').each(function(){
            let imagePos = $(this).offset().top;
            let topOfWindow = $(window).scrollTop();
            if (imagePos < topOfWindow+850) {
                $(this).addClass("animate__fadeInDown");
            }
        });
        $('.free_psd_h2').each(function(){
            let imagePos = $(this).offset().top;
            let topOfWindow = $(window).scrollTop();
            if (imagePos < topOfWindow+850) {
                $(this).addClass("animate__fadeInDown");
            }
        });
        $('.human_img').each(function(){
            let imagePos = $(this).offset().top;
            let topOfWindow = $(window).scrollTop();
            if (imagePos < topOfWindow+850) {
                $(this).addClass("animate__flipInY");
            }
        });
        $('.text_div').each(function(){
            let imagePos = $(this).offset().top;
            let topOfWindow = $(window).scrollTop();
            if (imagePos < topOfWindow+850) {
                $(this).addClass("animate__zoomInDown");
            }
        });
        $('.bulbozavr').each(function(){
            let imagePos = $(this).offset().top;
            let topOfWindow = $(window).scrollTop();
            if (imagePos < topOfWindow+850) {
                $(this).addClass("animate__zoomIn");
            }
        });
	});
    $('a.run').click(function () {
        let aClick = $(this).attr('href');
        let section = $(aClick).offset().top;
        $("body, html").animate({scrollTop: section}, 1000)
    });

});