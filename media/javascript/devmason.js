$(function() {
  Tabs.init();
  
  $('#header .search_form input').focus(function(e) {
    if (this.value == "Filter projects") {
      this.value = ""
    }
  });
  $('#header .search_form input').blur(function(e) {
    if (this.value == "") {
      this.value = "Filter projects"
    }
  });
  $('#header .search_form input').keyup(function(e) {
    project = $('#header .search_form input')[0].value;
    $('.site').each(function() {
        proj_name = this.children[0].textContent.trim();
        if (proj_name.indexOf(project) == -1) {
            this.style.display = 'none';
        }
        else {
        this.style.display = 'inline-block';
        }
    });
    /* e.preventDefault(); */
  });
});


var Tabs = {
  init: function() {
    tabs = $('.tab_group .tabs li a');

    // Hide all tab contents
    tabs_off = $('.tab_group .tabs li[class!=on] a');
    tab_hrefs = tabs_off.map(function() { return $(this).attr('href'); }).get().join(', ');
    if (tab_hrefs) {
      $(tab_hrefs).hide();
    }

    tabs.bind('click', this.click);
  },
  
  click: function(e) {
    e.preventDefault();
    target = $(this);
    tab_group = target.parents('.tab_group');
    
    // Hide tab content areas
    tabs = tab_group.find('.tabs li a');
    tabs.parent().removeClass('on')
    hrefs = tabs.map(function() { return $(this).attr('href'); }).get().join(', ')
    $(hrefs).hide();
    
    // Show clicked tab
    target.parent().addClass('on');
    $(target.attr('href')).show();
  }
}
