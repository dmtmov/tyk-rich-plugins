function preRequest(request, session, spec)
  tyk.req.set_header("Foo", "Bar")
  return request, session
end
