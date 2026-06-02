define i32 @pattern_casts_112(i16 %x, i16 %y) {
entry:
  %1 = or i16 %x, %y
  %2 = and i16 %1, 2
  %3 = zext i16 %2 to i32
  ret i32 %3
}