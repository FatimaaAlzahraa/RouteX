(function($){
  $(function(){
    console.log('[shipments] auto_submit_customer.js loaded');

    var KEY = 'shipment_auto_reload';
    if (sessionStorage.getItem(KEY) === '1') {
      sessionStorage.removeItem(KEY);
      console.log('[shipments] cleared reload flag');
    }

    function triggerReload(){
      var hidden = document.getElementById('id_customer');
      if (!hidden) {
        console.warn('[shipments] #id_customer not found at reload time');
        return;
      }
      var v = (hidden.value || '').trim();

      // 1) لو مفيش اختيار فعلي — متعملش reload
      if (!v) {
        console.log('[shipments] skip reload: empty value');
        return;
      }

      // 2) لو نفس القيمة موجودة بالفعل في الـ URL — متعملش reload
      var url = new URL(window.location.href);
      var current = (url.searchParams.get('customer') || '').trim();
      if (current === v) {
        console.log('[shipments] skip reload: same value in URL');
        return;
      }

      console.log('[shipments] trigger reload with customer=', v);
      url.searchParams.set('customer', v);
      sessionStorage.setItem(KEY, '1');
      window.location.href = url.toString();
    }

    // change على السيلكت الأصلي (حتى لو Select2 مغطّيه)
    $(document).on('change', '#id_customer', function(){
      console.log('[shipments] change on #id_customer');
      setTimeout(triggerReload, 0);
    });

    // حدث Select2 المخصص
    $(document).on('select2:select', '#id_customer', function(){
      console.log('[shipments] select2:select on #id_customer');
      setTimeout(triggerReload, 0);
    });
  });
})(django.jQuery);
