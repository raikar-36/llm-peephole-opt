define i32 @pattern_casts_117(i16 %x, i16 %y) {
entry:
  %0 = or i16 %x, %y
  %1 = and i16 %0, 7
  %2 = zext i16 %1 to i32
  ret i32 %2
}