define i32 @pattern_casts_118(i16 %x, i16 %y) {
entry:
  %1 = or i16 %x, %y
  %2 = and i16 %1, 8
  %3 = zext i16 %2 to i32
  ret i32 %3
}