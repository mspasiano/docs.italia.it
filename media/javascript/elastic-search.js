// Qs is defined on readthedocs/templates/docsitalia/overrides/search/elastic_search.html on bottom

$(document).ready(function () {
  $('#order-select').on('change', function () {
    var selectedOrder = $(this).children('option:selected').val()
    var params = Qs.parse(window.location.search.replace('?', ''))

    if (selectedOrder && selectedOrder !== 'relevance') {
      params.sort = selectedOrder
    } else {
      delete params.sort
    }

    window.location.href = window.location.origin + window.location.pathname + '?' + Qs.stringify(params)
  })
})
