/**
 * Full search screen
 * Reference to: https://github.com/italia/docs.italia.it/issues/314
 */

$(document).ready(function () {
  var modal = $('#modalSearchFullScreen')
  var input = $('#autocompleteSearchFullScreen')

  // Options
  // https://getbootstrap.com/docs/4.0/components/modal/#options
  modal.modal({
    backdrop: false,
    show: false
  })

  // Event triggered on open modal click
  modal.on('show.bs.modal', function () {
    $(document).scrollTop(0)
  })

  // Event triggered on open modal animation finished
  modal.on('shown.bs.modal', function () {
    input.focus()
  })

  // Event triggered on close modal click
  modal.on('hide.bs.modal', function () {

  })

  // Event triggered on close modal animation finished
  modal.on('hidden.bs.modal', function () {

  })

  input.on('change paste keyup', function () {
    var value = $(this).val()
    console.log(value)
 });
})
