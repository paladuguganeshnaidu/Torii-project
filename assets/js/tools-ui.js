// Small UI helpers for tools pages
(function(){
  function copyToClipboard(text){
    if(!navigator.clipboard) {
      const ta = document.createElement('textarea');
      ta.value = text; document.body.appendChild(ta); ta.select(); try{ document.execCommand('copy'); }catch(e){} ta.remove();
      return;
    }
    navigator.clipboard.writeText(text).catch(()=>{});
  }

  document.addEventListener('click', function(e){
    const t = e.target;
    if(t.matches('.copy-btn')){
      const target = t.dataset.target && document.querySelector(t.dataset.target);
      if(target) copyToClipboard(target.innerText || target.value || '');
      t.textContent = 'Copied';
      setTimeout(()=> t.textContent = 'Copy', 1200);
    }
  });

  // Enhance result toggle buttons
  document.addEventListener('click', function(e){
    const t = e.target;
    if(t.matches('.toggle-result')){
      const target = document.querySelector(t.dataset.target);
      if(!target) return;
      const visible = window.getComputedStyle(target).display !== 'none';
      target.style.display = visible ? 'none' : '';
      t.textContent = visible ? 'Show' : 'Hide';
    }
  });

})();
