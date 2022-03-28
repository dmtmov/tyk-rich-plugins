function preRequest(request, session, spec)
  tyk.req.set_header("Foo", "Barrr")
  return request, session
end
