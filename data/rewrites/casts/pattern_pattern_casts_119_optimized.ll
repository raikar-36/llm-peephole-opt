define i32 @pattern_casts_119(i16 %x, i16 %y) {
entry:
  %1 = and i16 %x, 9
  %2 = and i16 %y, 9
  %3 = or i16 %1, %2
  %4 = zext i16 %3 to i32
  ret i32 %4
}