$(document).ready(function () {
  var params = Qs.parse(window.location.search.replace('?', ''))

  var orderValues = ['date', '-date', 'name']

  if (params.sort && orderValues.includes(params.sort)) {
    $('#order-select').val(params.sort)
  }

  $('#order-select').change(function () {
    var selectedOrder = $(this).children('option:selected').val()
    var params = Qs.parse(window.location.search.replace('?', ''))

    if (selectedOrder) {
      params.sort = selectedOrder
    } else {
      if (params.sort) delete params.sort
    }

    window.location.href = window.location.origin + window.location.pathname + '?' + Qs.stringify(params)
  })
})
