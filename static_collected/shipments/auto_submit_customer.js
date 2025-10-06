(function($){
  $(function(){
    // عنصر العميل (الأصلي حتى لو select2 مغطيه)
    var $c = $('#id_customer');
    if(!$c.length) return;

    function reloadWithCustomer(){
      var v = ($c.val() || '').toString().trim();
      if (!v) return;                 // لو مفيش اختيار فعلي؛ سيبيه
      var url = new URL(window.location.href);
      url.searchParams.set('customer', v);
      // استخدمي replace عشان مايزوّدش الـhistory
      window.location.replace(url.toString());
    }

    // كفاية نسمع للـ change (بيتشغل في select2 كمان)
    $(document).on('change', '#id_customer', reloadWithCustomer);
    // ولو حابة تدعمي حدث select2 صراحةً
    $(document).on('select2:select', '#id_customer', reloadWithCustomer);
  });
})(django.jQuery);

