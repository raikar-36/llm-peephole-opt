define i32 @pattern_casts_123(i16 %x, i16 %y) {
entry:
  %0 = and i16 %x, 13
  %1 = and i16 %y, 13
  %2 = or i16 %0, %1
  %3 = zext i16 %2 to i32
  ret i32 %3
}