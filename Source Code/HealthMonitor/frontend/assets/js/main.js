function fetchJSON(url){
    return fetch(url).then(res=>res.json());
}
function renderList(elementId, items, formatter){
    const ul = document.getElementById(elementId);
    ul.innerHTML = '';
    items.forEach(i=>ul.innerHTML+=`<li>${formatter(i)}</li>`);
}
function renderLineChart(ctxId, labels, data, label){
    const ctx = document.getElementById(ctxId).getContext('2d');
    new Chart(ctx,{type:'line',data:{labels:labels,datasets:[{label:label,data:data,borderColor:'red',fill:false}]}})
}
