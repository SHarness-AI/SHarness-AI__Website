/* sharness.ai — nav interaction, the same component sgit.ai runs.
   Two jobs, and only one of them needs JavaScript on desktop: hover and :focus-within
   open a dropdown in CSS alone. This handles the rest — the phone menu button, and the
   fact that a finger has no hover. If this file never loads the nav still works: every
   group label is a link to that section's own page. */
(function () {
  'use strict';
  var nav = document.querySelector('nav.site');
  if (!nav) return;
  var toggle = nav.querySelector('.nav-toggle');
  nav.classList.add('js');           /* the phone menu folds its groups only when this file runs */
  function phone() { return toggle && window.getComputedStyle(toggle).display !== 'none'; }
  if (toggle) {
    toggle.addEventListener('click', function () {
      var open = nav.classList.toggle('open');
      toggle.setAttribute('aria-expanded', open ? 'true' : 'false');
      toggle.textContent = open ? 'Close' : 'Menu';
      /* Opening the menu opens the group the reader is in, so "where am I" is the first answer. */
      var here = nav.querySelector('.ni-has > .nl.here');
      if (open && here && !nav.querySelector('.ni-has.open')) here.parentNode.classList.add('open');
    });
  }
  /* The skip link's target: generated pages carry id="content" on <main>; a hand-written page
     gets it on its first <main>, or on its hero when it has none. */
  if (!document.getElementById('content')) {
    var target = document.querySelector('main') || document.querySelector('header.hero');
    if (target) { target.id = 'content'; target.setAttribute('tabindex', '-1'); }
  }
  /* On a touch screen the dropdown has no hover to open it: the first tap on a group
     label opens the menu, a second follows the link. Only where a dropdown is actually
     drawn — the collapsed phone menu folds its groups instead, below. */
  document.addEventListener('click', function (e) {
    var link = e.target.closest && e.target.closest('nav.site .ni-has > .nl');
    var open = nav.querySelector('.ni-has.open');
    /* A click elsewhere closes an open dropdown; inside the phone menu the groups fold only
       when their own label is tapped. */
    if (open && (!link || link.parentNode !== open) && !(phone() && nav.contains(e.target) && !link))
      open.classList.remove('open');
    /* In the phone menu a tap on a group label folds or unfolds it; the group's own page is
       its first item, so nothing becomes unreachable. */
    if (link && phone()) {
      e.preventDefault();
      link.parentNode.classList.toggle('open');
      return;
    }
    if (!link || !window.matchMedia || !window.matchMedia('(hover: none)').matches) return;
    var item = link.parentNode, sub = item.querySelector('.sub');
    if (sub && window.getComputedStyle(sub).position === 'absolute'
            && !item.classList.contains('open')) {
      e.preventDefault();
      item.classList.add('open');
    }
  });
  /* Escape closes whatever is open — keyboard users get out the same way everywhere. */
  document.addEventListener('keydown', function (e) {
    if (e.key !== 'Escape') return;
    var open = nav.querySelector('.ni-has.open');
    if (open) open.classList.remove('open');
    if (nav.classList.contains('open')) {
      nav.classList.remove('open');
      if (toggle) { toggle.setAttribute('aria-expanded', 'false'); toggle.textContent = 'Menu'; }
    }
  });
  /* On this page: the section being read is marked in the column beside the text: the last
     heading above a line 140px under the top, worked out once per frame while scrolling. */
  var side = document.querySelector('.toc-side');
  if (side) {
    var pairs = [];
    side.querySelectorAll('li a').forEach(function (a) {
      var h = document.getElementById(a.getAttribute('href').slice(1));
      if (h) pairs.push([h, a]);
    });
    var queued = false;
    var mark = function () {
      queued = false;
      var cur = pairs[0];
      pairs.forEach(function (p) { if (p[0].getBoundingClientRect().top < 140) cur = p; });
      pairs.forEach(function (p) { p[1].classList.toggle('on', p === cur); });
    };
    window.addEventListener('scroll', function () {
      if (!queued) { queued = true; window.requestAnimationFrame(mark); }
    }, { passive: true });
    if (pairs.length) mark();
  }
}());
