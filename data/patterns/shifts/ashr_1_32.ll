define i32 @pattern_ashr_1_32(i32 %x) {
entry:
  %result = ashr i32 %x, 1
  ret i32 %result
}
