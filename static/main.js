!(function($) {
  "use strict";

  // Preloader
  $(window).on('load', function() {
    if ($('#preloader').length) {
      $('#preloader').delay(10).fadeOut('fast', function() {
        $(this).remove();
      });
    }
  });

  // Init AOS
  function aos_init() {
    AOS.init({
      duration: 10,
      once: true
    });
  }
  $(window).on('load', function() {
    aos_init();
  });

})(jQuery);