$(() => {
  var status
  var streamingInterval
  var messages = []
  var prevReply = ""
  function displayMessages() {
    $("#messages").html("")
    messages.forEach((m) => {
      message = `<div class="message">
      <p>${m.role}: ${m.content}</p>
      </div>
      `
      $("#messages").append(message)
    })
  }

  function getStream() {
    if (status == "idle") {
      clearInterval(streamingInterval)
    }
    $.ajax({
      type: "GET",
      url: "http://127.0.0.1:5000/stream",
      success: (res) => {
        status = res.status
        // console.log(`res: ${res.text}, prev: ${prevReply}`)

        messages[messages.length - 1].content = res.text
        // console.log(res.text)
        // $("#messages").text(res.text)
        displayMessages()
      }
    })
  }

  $("#input").keypress((event) => {
    if (event.key === "Enter") {
      event.preventDefault()
      if (status == "generating") {
        return
      }
      $.ajax({
        type: "POST",
        url: "http://127.0.0.1:5000/generate",
        data: JSON.stringify({
          "message": $("#input").val(),
          "role": "User"
        }),
        contentType: 'application/json',
        success: () => {
          status = "generating"
          messages.push({
            "role": "User",
            "content": $("#input").val()
          })
          $("#input").val("")
          messages.push({
            "role": "Assistant",
            "content": ""
          })
          streamingInterval = setInterval(getStream, 100)
        }
      })
    }
    if (event.key === "Enter" && event.shiftKey) {
      $("#input").val($("#input").val() + '\n')
    }
  })
})