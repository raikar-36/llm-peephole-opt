define i32 @pattern_and_neg2_32(i32 %x) {
entry:
  %result = and i32 %x, -2
  ret i32 %result
}
