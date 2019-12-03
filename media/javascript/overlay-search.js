/**
 * Overlay search
 * Reference to: https://github.com/italia/docs.italia.it/issues/314
 */

var debounceInputTiming = 300
var params = {
  filter: 'all',
  search: ''
}

var pendingRequest = null
var fetchResultsFromApi = function () {
  // TODO: Fetch here results from API
  if (pendingRequest) pendingRequest.abort('Canceled from user')

  // console.log('Fetch API with those params', params)

  pendingRequest = $.ajax('https://jsonplaceholder.typicode.com/users')
    .done(function (response) {
      // console.log('response', response)
    })
    .fail(function (error) {
      if (error.statusText !== 'Canceled from user') {
        console.log('fetchResultsFromApi error:', error)
      }
    })
}

$(document).ready(function () {
  var modal = $('#modalSearchFullScreen')
  var input = $('#autocompleteSearchFullScreen')
  var tagButtons = $('.sfs-btn-tag')

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

  input.on('paste keyup', debounce(function () {
    params.search = $(this).val()
    fetchResultsFromApi()
  }, debounceInputTiming))

  tagButtons.on('click', function () {
    var filter = $(this).attr('data-filter')
    params.filter = filter

    tagButtons.each(function (index, button) {
      $(this).removeClass('btn-primary btn-outline-secondary')

      var isActive = $(this).attr('data-filter') === filter
      $(this).addClass(isActive ? 'btn-primary' : 'btn-outline-secondary')

      var icon = button.querySelector('.icon')
      if (icon) icon.setAttribute('class', isActive ? 'icon icon-white' : 'icon icon-secondary')
    })

    fetchResultsFromApi()
  })
})

// Returns a function, that, as long as it continues to be invoked, will not
// be triggered. The function will be called after it stops being called for
// N milliseconds. If `immediate` is passed, trigger the function on the
// leading edge, instead of the trailing.
var debounce = function (func, wait, immediate) {
  var timeout

  return function () {
    var context = this
    var args = arguments

    var later = function () {
      timeout = null
      if (!immediate) func.apply(context, args)
    }

    var callNow = immediate && !timeout
    clearTimeout(timeout)
    timeout = setTimeout(later, wait)

    if (callNow) {
      func.apply(context, args)
    }
  }
}
