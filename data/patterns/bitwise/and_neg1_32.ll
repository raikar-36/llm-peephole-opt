define i32 @pattern_and_neg1_32(i32 %x) {
entry:
  %result = and i32 %x, -1
  ret i32 %result
}
