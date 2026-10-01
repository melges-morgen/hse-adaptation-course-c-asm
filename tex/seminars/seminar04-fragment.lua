-- The full handbook has its own title; the main course already has a seminar heading.
function Header(header)
  if header.level == 1 then return {} end
  header.level = header.level + 1
  return header
end
