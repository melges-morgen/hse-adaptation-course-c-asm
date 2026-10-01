-- Fixed widths make the approach comparison readable in both A4 editions.
function Table(tbl)
  if #tbl.colspecs == 3 then
    local widths = {0.18, 0.39, 0.39}
    for index, column in ipairs(tbl.colspecs) do
      column[2] = widths[index]
      tbl.colspecs[index] = column
    end
  end
  return tbl
end
