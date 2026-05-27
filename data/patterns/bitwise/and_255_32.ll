define i32 @pattern_and_255_32(i32 %x) {
entry:
  %result = and i32 %x, 255
  ret i32 %result
}
