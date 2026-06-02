define i32 @pattern_casts_111(i16 %x, i16 %y) {
entry:
  %0 = and i16 %x, 1
  %1 = and i16 %y, 1
  %2 = zext i16 %0 to i32
  %3 = zext i16 %1 to i32
  %4 = or i32 %2, %3
  ret i32 %4
}