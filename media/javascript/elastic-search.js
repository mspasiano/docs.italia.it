$(document).ready(function () {
  $('#order-select').change(function () {
    var selectedOrder = $(this).children('option:selected').val()
    var params = Qs.parse(window.location.search.replace('?', ''))

    if (selectedOrder && selectedOrder !== 'relevance') {
      params.sort = selectedOrder
    } else {
      if (params.sort) delete params.sort
    }

    window.location.href = window.location.origin + window.location.pathname + '?' + Qs.stringify(params)
  })
})
