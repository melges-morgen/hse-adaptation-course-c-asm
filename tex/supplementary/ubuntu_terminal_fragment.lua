-- The full course has its own part and chapter headings.
function Header(header)
  if header.level == 1 then return {} end
  header.level = header.level - 1
  return header
end

-- Give the command table room for Russian explanations in the 14pt book.
function Table(tbl)
  if #tbl.colspecs == 2 then
    tbl.colspecs[1] = {tbl.colspecs[1][1], 0.37}
    tbl.colspecs[2] = {tbl.colspecs[2][1], 0.59}
  end
  return tbl
end
