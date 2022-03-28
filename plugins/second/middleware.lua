function preRequest(request, session, spec)
  tyk.req.set_header("Fooo", "Barrr")
  return request, session
end
