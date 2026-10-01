-- Set explicit column widths for compact A4 handbooks and the course PDF.
function Table(tbl)
  local widths = {
    [3] = {0.16, 0.16, 0.64},
    [5] = {0.07, 0.07, 0.26, 0.34, 0.22},
  }
  local selected = widths[#tbl.colspecs]
  if selected then
    for index, column in ipairs(tbl.colspecs) do
      column[2] = selected[index]
      tbl.colspecs[index] = column
    end
  end
  return tbl
end
